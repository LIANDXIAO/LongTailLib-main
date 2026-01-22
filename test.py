import torch
print(f"PyTorch 版本: {torch.__version__}")
if torch.cuda.is_available():
    print(f"✅ 成功！检测到显卡: {torch.cuda.get_device_name(0)}")
else:
    print("❌ 失败，未检测到显卡")