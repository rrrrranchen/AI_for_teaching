# -*- coding: utf-8 -*-


print("根据提供的参考资料，以下是 Jetson Nano 安装 TensorFlow GPU 版本的完整步骤：\n\n### 📦 安装准备\n1. **硬件要求**：\n   - 使用大容量高速 microSD 卡（建议 ≥64GB UHS-1）\n   - 使用高品质 5V/2A 电源适配器\n   - 推荐使用 NVIDIA AC8265 双模无线网卡（可选）\n   - 确认设备型号：B02 版本有两路 CSI 相机接口\n\n2. **系统要求**：\n   - 已刷写官方 Jetson Nano 镜像\n   - 确认 CUDA 环境已正确安装（JetPack 默认包含）\n   - 通过 `nvcc -v` 验证 CUDA 版本（示例输出：`release 10.2, V10.2.89`）\n\n---\n\n### ⚙️ 安装 TensorFlow GPU 步骤\n1. **安装系统依赖包**：\n   ```bash\n   sudo apt-get update\n   sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev \\\n   zlib1g-dev zip libjpeg9-dev liblapack-dev libblas-dev gfortran\n   ```\n\n2. **安装并升级 pip3**：\n   ```bash\n   sudo apt-get install python3-pip\n   sudo python3 -m pip install --upgrade pip\n   sudo pip3 install -U testresources setuptools==65.5.0\n   ```\n\n3. **安装 Python 依赖包**：\n   ```bash\n   sudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 \\\n   keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 \\\n   protobuf pybind11 cython pkgconfig packaging h5py==3.6.0\n   ```\n\n4. **安装 TensorFlow GPU 版本**：\n   ```bash\n   sudo pip3 install --extra-index-url \\\n   https://developer.download.nvidia.com/compute/redist/jp/v51 \\\n   tensorflow==2.11.0+nv23.01\n   ```\n   > 💡 **版本注意**：TensorFlow 版本必须与 JetPack 版本匹配\n\n5. **验证安装**：\n   ```bash\n   python3 -c \"import tensorflow as tf; print(tf.__version__)\"\n   ```\n   ✅ 预期输出：`2.11.0` 及相关 CUDA 库加载信息\n\n---\n\n### ⚠️ 注意事项\n1. **资源限制处理**：\n   - 训练时若出现 `OOM when allocating tensor` 错误：\n     - 减小模型 `batch_size` 值\n     - 使用轻量级模型（如 MobileNet）\n     ```python\n     # 示例：减小 batch_size\n     model.fit(..., batch_size=16)  # 避免使用过大值\n     ```\n\n2. **VNC 远程协助**（可选）：\n   ```bash\n   # 安装 VNC 服务\n   sudo apt install vino\n   \n   # 配置自动登录\n   mkdir -p ~/.config/autostart\n   cp /usr/share/applications/vino-server.desktop ~/.config/autostart/\n   ```\n\n3. **模型部署实践**：\n   - 使用 TensorFlow Lite 部署到边缘设备\n   - 示例流程：\n     ```mermaid\n     graph LR\n     A[训练模型] --> B[转换为.tflite格式]\n     B --> C[复制到Jetson Nano]\n     C --> D[使用OpenCV/TFLite加载]\n     D --> E[实时推理]\n     ```\n\n---\n\n### 🔍 验证 GPU 加速\n检查 TensorFlow 是否识别到 GPU：\n```python\nimport tensorflow as tf\nprint(\"GPU Available:\", tf.config.list_physical_devices('GPU'))\n# 预期输出： [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]\n```\n\n> ⚠️ **重要提示**：若需使用 OpenCV 的 GPU 加速功能，需额外编译支持 CUDA 的 OpenCV 版本（默认 JetPack 安装的 OpenCV 不支持 GPU 加速）")
import numpy as np

# 输入数据（假设为二维数组或列表的列表）
data = [
    [0.8697, 0.8769, 0.8733, 0.8678],
    [0.8798, 0.8867, 0.8832, 0.9023],
    [0.8901, 0.8976, 0.8938, 0.8435],
    [0.8829, 0.9241, 0.9030, 0.8798],
    [0.8521, 0.9156, 0.8827, 0.8929],
    [0.8659, 0.8785, 0.8722, 0.8237],
    [0.8769, 0.8859, 0.8814, 0.8269],
    [0.8862, 0.9324, 0.9087, 0.9249],
    [0.8913, 0.9165, 0.9037, 0.8781],
    [0.8723, 0.9217, 0.8963, 0.8538]
]

# 转换为NumPy数组
data = np.array(data)

# 计算每列平均值（保留4位小数）
averages = np.mean(data, axis=0).round(4)

# 打印结果
print("指标\t\t平均值")
print("="*25)
print(f"精确度(P)\t{averages[0]}")
print(f"召回率(R)\t{averages[1]}")
print(f"F1值\t\t{averages[2]}")
print(f"BLEURT得分\t{averages[3]}")

