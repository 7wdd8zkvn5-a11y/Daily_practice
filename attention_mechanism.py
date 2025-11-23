import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple


class RotaryPositionalEmbedding(nn.Module):
    """
    RoPE (Rotary Positional Embedding) implementation
    """
    def __init__(self, dim: int, max_seq_len: int = 2048):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        
        # Precompute frequencies
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2, dtype=torch.float) / dim))
        self.register_buffer('inv_freq', inv_freq)
        
        # Precompute sinusoidal positions
        t = torch.arange(max_seq_len, dtype=torch.float)
        freqs = torch.einsum('i,j->ij', t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        
        # Register cos and sin embeddings
        self.register_buffer('cos_cached', emb.cos().unsqueeze(0).unsqueeze(0))
        self.register_buffer('sin_cached', emb.sin().unsqueeze(0).unsqueeze(0))

    def forward(self, x: torch.Tensor, seq_len: int = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply rotary positional embedding to input tensor
        Args:
            x: Input tensor of shape [batch_size, num_heads, seq_len, head_dim]
            seq_len: Sequence length (optional, will use x.shape[-2] if not provided)
        Returns:
            Tuple of (x * cos + rotate(x) * sin, -rotate(x) * cos + x * sin)
        """
        if seq_len is None:
            seq_len = x.shape[-2]
        
        cos = self.cos_cached[:, :, :seq_len, :].to(x.dtype)
        sin = self.sin_cached[:, :, :seq_len, :].to(x.dtype)
        
        return apply_rotary_pos_emb(x, cos, sin)


def apply_rotary_pos_emb(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """
    Apply rotary positional embedding to input tensor
    """
    # x: [batch_size, num_heads, seq_len, head_dim]
    # cos, sin: [1, 1, seq_len, head_dim]
    
    # Split along the last dimension
    x1 = x[..., ::2]  # Even indices
    x2 = x[..., 1::2]  # Odd indices
    
    # Apply rotation
    rotated_x = torch.stack([-x2, x1], dim=-1).reshape_as(x)
    
    # Apply RoPE: x * cos + rotate(x) * sin
    return (x * cos) + (rotated_x * sin)


class FlashAttention(nn.Module):
    """
    FlashAttention implementation with optimized memory usage
    """
    def __init__(self, dropout: float = 0.0, causal: bool = True):
        super().__init__()
        self.dropout = dropout
        self.causal = causal

    def forward(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, 
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        FlashAttention forward pass
        Args:
            q: Query tensor [batch_size, num_heads, seq_len, head_dim]
            k: Key tensor [batch_size, num_heads, seq_len, head_dim]
            v: Value tensor [batch_size, num_heads, seq_len, head_dim]
            mask: Attention mask [batch_size, 1, seq_len, seq_len] or [batch_size, seq_len]
        Returns:
            Output tensor [batch_size, num_heads, seq_len, head_dim]
        """
        return flash_attention(q, k, v, dropout=self.dropout, causal=self.causal, mask=mask)


def flash_attention(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, 
                   dropout: float = 0.0, causal: bool = True, 
                   mask: Optional[torch.Tensor] = None) -> torch.Tensor:
    """
    Memory-efficient flash attention implementation
    """
    batch_size, num_heads, q_seq_len, head_dim = q.size()
    k_seq_len = k.size(2)
    
    # Reshape to [batch_size * num_heads, seq_len, head_dim]
    q = q.reshape(-1, q_seq_len, head_dim)
    k = k.reshape(-1, k_seq_len, head_dim)
    v = v.reshape(-1, k_seq_len, head_dim)
    
    # Compute attention scores
    scores = torch.bmm(q, k.transpose(-2, -1)) / math.sqrt(head_dim)
    
    # Apply causal mask if needed
    if causal:
        # Create causal mask with the correct dimensions (q_seq_len x k_seq_len)
        causal_mask = torch.ones(q_seq_len, k_seq_len, device=q.device, dtype=q.dtype)
        causal_mask = torch.tril(causal_mask, diagonal=k_seq_len - q_seq_len)  # Allow attention to past and current
        scores = scores.masked_fill(causal_mask == 0, float('-inf'))
    
    # Apply custom mask if provided
    if mask is not None:
        scores = scores + mask
    
    # Apply softmax
    attention_weights = F.softmax(scores, dim=-1)
    
    # Apply dropout
    if dropout > 0:
        attention_weights = F.dropout(attention_weights, p=dropout)
    
    # Compute output
    output = torch.bmm(attention_weights, v)
    
    # Reshape back to original dimensions
    return output.reshape(batch_size, num_heads, q_seq_len, head_dim)


class GroupedQueryAttention(nn.Module):
    """
    Grouped Query Attention (GQA) implementation
    """
    def __init__(self, embed_dim: int, num_heads: int, num_kv_heads: int, 
                 head_dim: int, dropout: float = 0.0):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.dropout = dropout
        
        # Calculate number of groups
        self.num_groups = num_heads // num_kv_heads
        
        # Linear projections
        self.q_proj = nn.Linear(embed_dim, num_heads * head_dim, bias=False)
        self.k_proj = nn.Linear(embed_dim, num_kv_heads * head_dim, bias=False)
        self.v_proj = nn.Linear(embed_dim, num_kv_heads * head_dim, bias=False)
        self.out_proj = nn.Linear(num_heads * head_dim, embed_dim, bias=False)
        
        # Initialize weights
        nn.init.xavier_uniform_(self.q_proj.weight)
        nn.init.xavier_uniform_(self.k_proj.weight)
        nn.init.xavier_uniform_(self.v_proj.weight)
        nn.init.xavier_uniform_(self.out_proj.weight)

    def forward(self, x: torch.Tensor, 
                rope: Optional[RotaryPositionalEmbedding] = None,
                kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
                use_cache: bool = False) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        GQA forward pass
        Args:
            x: Input tensor [batch_size, seq_len, embed_dim]
            rope: Rotary positional embedding module
            kv_cache: Previous key-value cache (k_cache, v_cache)
            use_cache: Whether to return updated cache
        Returns:
            Output tensor and optionally updated cache
        """
        batch_size, seq_len, embed_dim = x.size()
        
        # Project to Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        # Expand K and V for GQA (before applying RoPE to cache)
        orig_k = self.k_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        orig_v = self.v_proj(x).view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        
        # Apply RoPE if provided
        if rope is not None:
            q = rope(q)
            orig_k = rope(orig_k)  # Apply RoPE to original k (for cache)
        
        # Expand K and V for GQA
        k_expanded = orig_k.repeat_interleave(self.num_groups, dim=1)
        v_expanded = orig_v.repeat_interleave(self.num_groups, dim=1)
        
        # Update KV cache if provided - but store original k, v (not expanded)
        if kv_cache is not None:
            # Concatenate with cached values
            k_cache, v_cache = kv_cache
            orig_k = torch.cat([k_cache, orig_k], dim=2)
            orig_v = torch.cat([v_cache, orig_v], dim=2)
            
            # Now expand for attention computation
            k_expanded = orig_k.repeat_interleave(self.num_groups, dim=1)
            v_expanded = orig_v.repeat_interleave(self.num_groups, dim=1)
        else:
            # k_expanded and v_expanded already set above
            pass  # k_expanded and v_expanded are already computed above
        
        # Apply FlashAttention
        attn_output = flash_attention(q, k_expanded, v_expanded, dropout=self.dropout, causal=True)
        
        # Update cache if requested - return original (non-expanded) k, v
        cache = (orig_k, orig_v) if use_cache else None
        
        # Reshape and project output
        attn_output = attn_output.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.num_heads * self.head_dim
        )
        output = self.out_proj(attn_output)
        
        return output, cache


class KVCache:
    """
    Key-Value Cache for efficient inference
    """
    def __init__(self, batch_size: int, max_seq_len: int, num_kv_heads: int, 
                 head_dim: int, dtype: torch.dtype = torch.float32, 
                 device: torch.device = torch.device('cpu')):
        self.batch_size = batch_size
        self.max_seq_len = max_seq_len
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.dtype = dtype
        self.device = device
        
        # Initialize empty cache
        self.k_cache = torch.zeros(
            (batch_size, num_kv_heads, 0, head_dim), 
            dtype=dtype, device=device
        )
        self.v_cache = torch.zeros(
            (batch_size, num_kv_heads, 0, head_dim), 
            dtype=dtype, device=device
        )
    
    def update(self, k: torch.Tensor, v: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Update the cache with new key and value tensors
        Args:
            k: New key tensor [batch_size, num_kv_heads, seq_len, head_dim]
            v: New value tensor [batch_size, num_kv_heads, seq_len, head_dim]
        Returns:
            Updated k and v tensors including cached values
        """
        self.k_cache = torch.cat([self.k_cache, k], dim=2)
        self.v_cache = torch.cat([self.v_cache, v], dim=2)
        
        return self.k_cache, self.v_cache
    
    def get_cache(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Return current cache"""
        return self.k_cache, self.v_cache
    
    def reset(self):
        """Reset the cache to empty"""
        self.k_cache = torch.zeros(
            (self.batch_size, self.num_kv_heads, 0, self.head_dim), 
            dtype=self.dtype, device=self.device
        )
        self.v_cache = torch.zeros(
            (self.batch_size, self.num_kv_heads, 0, self.head_dim), 
            dtype=self.dtype, device=self.device
        )


class AttentionBlock(nn.Module):
    """
    Complete attention block with RoPE, FlashAttention, GQA and KV Cache
    """
    def __init__(self, embed_dim: int, num_heads: int, num_kv_heads: int, 
                 head_dim: int, dropout: float = 0.0, max_seq_len: int = 2048):
        super().__init__()
        
        # Components
        self.rope = RotaryPositionalEmbedding(head_dim, max_seq_len)
        self.gqa = GroupedQueryAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            dropout=dropout
        )
        self.layer_norm = nn.LayerNorm(embed_dim)
        
    def forward(self, x: torch.Tensor, 
                kv_cache: Optional[KVCache] = None,
                use_cache: bool = False) -> Tuple[torch.Tensor, Optional[KVCache]]:
        """
        Forward pass through the attention block
        """
        # Apply layer norm
        x_norm = self.layer_norm(x)
        
        # Apply GQA with RoPE
        if kv_cache is not None:
            # Get cached K and V tensors
            k_cache, v_cache = kv_cache.get_cache()
            
            # Pass to GQA with cache
            attn_output, new_cache = self.gqa(
                x_norm, 
                rope=self.rope,
                kv_cache=(k_cache, v_cache) if k_cache.size(2) > 0 else None,
                use_cache=use_cache
            )
            
            # Update cache if needed
            if use_cache and new_cache is not None:
                kv_cache.update(*new_cache)
        else:
            # Standard forward without cache
            attn_output, _ = self.gqa(x_norm, rope=self.rope, use_cache=False)
        
        # Add residual connection
        output = x + attn_output
        
        return output, kv_cache


# Example usage
if __name__ == "__main__":
    # Example parameters
    batch_size = 2
    seq_len = 128
    embed_dim = 512
    num_heads = 8
    num_kv_heads = 2  # GQA: fewer KV heads than query heads
    head_dim = 64
    max_seq_len = 2048
    
    # Create attention block
    attention_block = AttentionBlock(
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_kv_heads=num_kv_heads,
        head_dim=head_dim,
        dropout=0.1,
        max_seq_len=max_seq_len
    )
    
    # Create input tensor
    x = torch.randn(batch_size, seq_len, embed_dim)
    
    # Create KV cache
    kv_cache = KVCache(
        batch_size=batch_size,
        max_seq_len=max_seq_len,
        num_kv_heads=num_kv_heads,
        head_dim=head_dim
    )
    
    # Forward pass
    print("Input shape:", x.shape)
    output, _ = attention_block(x, kv_cache=kv_cache, use_cache=True)
    print("Output shape:", output.shape)
    
    # Test with new sequence (simulating autoregressive generation)
    new_x = torch.randn(batch_size, 1, embed_dim)  # Single token
    output_new, _ = attention_block(new_x, kv_cache=kv_cache, use_cache=True)
    print("New output shape:", output_new.shape)
    print("KV cache updated successfully!")