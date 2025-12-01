import paddle
from paddleocr import PaddleOCR

def main():
    # 1. 环境检查
    print("PaddlePaddle 版本:", paddle.__version__)
    print("CUDA 可用:", paddle.is_compiled_with_cuda())

    # 2. 初始化 OCR（关闭文档校正以加速）
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False
    )
    print("OCR 初始化成功！\n")

    # 3. 指定图片路径（Windows 路径）
    # 注意：使用原始字符串 r"" 避免转义问题
    image_path = r"D:\Backup\Downloads\123.jpeg"

    # 4. 执行识别
    try:
        results = ocr.predict(input=image_path)
        
        # 5. 遍历结果（3.x 返回可迭代对象）
        for idx, res in enumerate(results):
            print(f"--- 识别结果 {idx + 1} ---")
            
            # 打印详细信息（文本、置信度、坐标）
            res.print()
            
            # 6. 保存结果（可选）
            output_dir = "output"
            res.save_to_img(output_dir)   # 保存可视化图片
            res.save_to_json(output_dir)  # 保存JSON数据
            print(f"结果已保存到 '{output_dir}' 目录\n")
            
            # 7. 仅提取文本（如果需要）
            if 'rec_text' in res:
                print("提取的文本内容:")
                for line in res['rec_text']:
                    print(f"  {line}")

    except Exception as e:
        print(f"识别失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()