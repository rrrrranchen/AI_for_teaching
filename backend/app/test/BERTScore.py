# -*- coding: utf-8 -*-
import os
import re
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from bert_score import BERTScorer

def preprocess_text(text):
    """清理Markdown标签和冗余提示"""
    text = re.sub(r'^(BASH|PYTHON|TEXT)\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'✅.*?\n|📌.*?\n', '', text)
    return text.strip()

scorer = BERTScorer(lang="zh", model_type="bert-base-multilingual-cased")

def evaluate_bertscore(candidates, references):
    """预处理后评估"""
    processed_cands = [preprocess_text(c) for c in candidates]
    processed_refs = [preprocess_text(r) for r in references]
    P, R, F1 = scorer.score(processed_cands, processed_refs)
    return {'bert_precision': P.tolist(), 'bert_recall': R.tolist(), 'bert_f1': F1.tolist()}

# 示例：对比生成的答案与知识库最佳匹配条目
knowledge_base = [
    # 分块1: TensorFlow.js模型构建方式
    """根据提供的参考资料，在Jetson Nano上安装TensorFlow GPU版本的完整步骤如下：\n\n---\n\n### 📋 **安装准备**\n1. **硬件要求**  \n   - 使用64GB UHS-1级microSD卡作为主存储器\n   - 配备5V/2A高品质电源（USB供电仅支持5W模式，10W模式需外接电源）\n   - 官方推荐无线网卡：AC8265双模网卡（支持2.4G/5G和蓝牙4.2）\n   - 可选树莓派摄像头（IMX219模组，800万像素）\n\n---\n\n### ⚙️ **安装步骤**\n\n#### 1. **安装系统依赖包**\n```bash\nsudo apt-get update\nsudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev \\\n                     zlib1g-dev zip libjpeg9-dev \\\n                     liblapack-dev libblas-dev gfortran\n```\n\n#### 2. **安装并升级pip3**\n```bash\nsudo apt-get install python3-pip\nsudo python3 -m pip install --upgrade pip\nsudo pip3 install -U testresources setuptools==65.5.0\n```\n\n#### 3. **安装Python依赖项**\n```bash\nsudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 \\\n                  keras_preprocessing==1.1.2 keras_applications==1.0.8 \\\n                  gast==0.4.0 protobuf pybind11 cython pkgconfig packaging \\\n                  h5py==3.6.0\n```\n\n#### 4. **验证CUDA安装**\n```bash\nnvcc -v\n```\n✅ 预期输出示例：  \n`Cuda compilation tools, release 10.2, V10.2.89`\n\n#### 5. **安装TensorFlow GPU**\n```bash\nsudo pip3 install --extra-index-url \\\nhttps://developer.download.nvidia.com/compute/redist/jp/v51 \\\ntensorflow==2.11.0+nv23.01\n```\n> ⚠️ **版本注意**：TensorFlow版本必须与JetPack版本匹配（参考[NVIDIA官方文档](https://developer.nvidia.com/embedded/jetpack)）\n\n#### 6. **验证安装**\n```python\npython3 -c \"import tensorflow as tf; print(tf.__version__)\"\n```\n✅ 预期输出：  \n```\n2023-04-20 10:01:13.231340: I tensorflow/stream_executor/platform/default/dso_loader.cc:49] Successfully opened dynamic library libcudart.so.10.2\n2.11.0\n```\n\n---\n\n### ⚠️ **关键注意事项**\n1. **CUDA要求**  \n   安装前必须确保CUDA已正确配置（通过`nvcc -v`验证）\n\n2. **资源限制**  \n   Jetson Nano的4GB内存部分用于显存共享：\n   - 训练模型时可能遇到内存溢出（OOM）错误：\n     ```bash\n     OOM when allocating tensor with shape [64,96,112,112]\n     ```\n   - 解决方案：减小`batch_size`或使用轻量级模型\n\n3. **模型部署**  \n   - 推荐使用TensorFlow Lite进行边缘部署（参考材料8.5.3节）\n   - 典型工作流：\n     ```mermaid\n     graph LR\n     A[在PC训练模型] --> B[转换为TFLite格式]\n     B --> C[复制到Jetson Nano]\n     C --> D[部署推理]\n     ```\n\n---\n\n### 🔍 **故障排查**\n- **安装失败**：检查JetPack版本与TensorFlow版本的兼容性\n- **导入错误**：确认CUDA路径已正确配置（`export LD_LIBRARY_PATH=/usr/local/cuda/lib64`）\n- **性能问题**：使用`jtop`工具监控系统资源（图9-13）\n\n> 💡 **提示**：完整环境配置后，可参考材料8.3.3节设置VNC服务器实现无头（headless）远程操作。"""
]


generated_answer = """
根据提供的参考资料，以下是 Jetson Nano 安装 TensorFlow GPU 版本的完整步骤和注意事项：\n\n### 🛠️ 安装准备\n1. **硬件要求**：\n   - 使用 **64GB UHS-1 microSD卡** 作为启动设备和主存储\n   - 配备 **5V/2A 高品质电源**（电源不稳定会导致系统崩溃）\n   - 推荐使用 NVIDIA 官方认证的 AC8265 双模网卡（支持 2.4G/5G 和蓝牙 4.2）\n\n2. **电源模式选择**：\n   ```bash\n   # 切换到10W高性能模式（必须使用PowerJack供电）\n   sudo nvpmodel -m 0\n   # 切换到5W低功耗模式（可用Micro-USB供电）\n   sudo nvpmodel -m 1\n   ```\n\n---\n\n### 📥 安装 TensorFlow GPU 步骤\n\n#### 步骤 1：安装系统依赖包\n```bash\nsudo apt-get update\nsudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev \\\nzlib1g-dev zip libjpeg9-dev liblapack-dev libblas-dev gfortran\n```\n\n#### 步骤 2：安装并升级 pip3\n```bash\nsudo apt-get install python3-pip\nsudo python3 -m pip install --upgrade pip\nsudo pip3 install -U testresources setuptools==65.5.0\n```\n\n#### 步骤 3：安装 Python 依赖项\n```bash\nsudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 \\\nkeras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 \\\nprotobuf pybind11 cython pkgconfig packaging h5py==3.6.0\n```\n\n#### 步骤 4：确认 CUDA 安装\n```bash\nnvcc -v\n```\n正常输出应显示 CUDA 版本信息（如示例）：\n```\nnvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2019 NVIDIA Corporation\nBuilt On Wed_Oct_23_21:14:42_PDT_2019\nCuda compilation tools, release 10.2, V10.2.89\n```\n\n#### 步骤 5：安装 TensorFlow GPU 版本\n```bash\nsudo pip3 install --extra-index-url \\\nhttps://developer.download.nvidia.com/compute/redist/jp/v51 \\\ntensorflow==2.11.0+nv23.01\n```\n> ⚠️ **版本注意**：必须选择与 JetPack 版本兼容的 TensorFlow 版本（参考[官方兼容表](https://developer.nvidia.com/embedded/jetpack)）\n\n#### 步骤 6：验证安装\n```python\npython3\n>>> import tensorflow as tf\n>>> print(tf.__version__)\n```\n预期输出：\n```\n2.11.0\n2023-04-20 10:01:13.231340: I tensorflow/stream_executor/platform/default/dso_loader.cc:49] Successfully opened dynamic library libcudart.so.10.2\n```\n\n---\n\n### ⚠️ 关键注意事项\n1. **CUDA 预配置要求**：\n   - TensorFlow GPU 版本安装前**必须确保 CUDA 已正确配置**\n   - JetPack 默认包含 CUDA，使用 `nvcc -v` 验证\n\n2. **资源限制处理**：\n   - 训练时若遇内存溢出（如 `OOM when allocating tensor`）：\n     ```python\n     # 减小 batch_size 值\n     model.fit(..., batch_size=16)  # 默认64可能导致OOM\n     ```\n   - 使用轻量级模型（如 MobileNetV2）替代大型模型\n\n3. **部署优化**：\n   - 推荐使用 TensorFlow Lite 在 Jetson Nano 部署模型：\n     ```python\n     converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)\n     tflite_model = converter.convert()\n     with open('model.tflite', 'wb') as f:\n         f.write(tflite_model)\n     ```\n   - 通过 VNC 实现 headless 远程访问（参考 8.3.3 节配置）\n\n---\n\n### 🔧 故障排除\n| 问题现象 | 解决方案 |\n|---------|----------|\n| `ImportError: libcudart.so.10.2` | 执行 `sudo apt install libcudart10.2` |\n| 安装过程卡死 | 检查电源是否达到 5V/2A 要求 |\n| `pip3 install` 超时 | 使用国内镜像源：`pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple ...` |\n| 训练时 GPU 未启用 | 检查日志中是否出现 `Successfully opened dynamic library libcuda.so` |\n\n> 💡 **最佳实践**：安装完成后立即测试 GPU 加速效果：\n> ```python\n> tf.config.list_physical_devices('GPU')  # 应返回GPU设备信息\n> ```
"""
all_scores = []
for i, reference in enumerate(knowledge_base):
    scores = evaluate_bertscore([generated_answer], [reference])
    all_scores.append({'index': i, 'scores': scores})

# 输出结果
for score in all_scores:
    print(f"\nKnowledge Base Entry {score['index']+1}:")
    print("="*50)
    print(f"Precision: {score['scores']['bert_precision'][0]:.4f}")
    print(f"Recall:    {score['scores']['bert_recall'][0]:.4f}") 
    print(f"F1:        {score['scores']['bert_f1'][0]:.4f}")
    print("="*50)
