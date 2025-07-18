# -*- coding: utf-8 -*-

import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 设置环境变量

from bert_score import BERTScorer

# 加载多语言模型（中文需用'bert-base-multilingual-cased'）
scorer = BERTScorer(lang="zh", model_type="bert-base-chinese")

def evaluate_bertscore(candidates, references):
    """ 批量评估生成内容与知识库条目的关联性 """
    P, R, F1 = scorer.score(candidates, references)
    return {
        'bert_precision': P.tolist(),  # 检测生成内容是否基于知识库
        'bert_recall': R.tolist(),    # 检测知识库内容是否被完整覆盖
        'bert_f1': F1.tolist()        # 综合指标
    }

# 示例：对比生成的答案与知识库最佳匹配条目
knowledge_base = [
    # 分块1: TensorFlow.js模型构建方式
    """TensorFlow是一个使用数据流图进行数值计算的开源软件库，这种灵活的架构可以将模型部署到桌面、服务器或移动设备中的CPU 或 GPU上。下面将在Jetson Nano安装TensorFlow GPU版本，安装TensorFlow GPU版本需要成功配置好CUDA。不过在安装TensorFlow GPU之前，需要安装依赖项。
1)安装 TensorFlow 所需的系统包
#sudo apt-get update
#sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg9-dev liblapack-dev libblas-dev gfortran
2)安装和升级pip3
#sudo apt-get install python3-pip
#sudo python3 -m pip install --upgrade pip
#sudo pip3 install -U testresources setuptools==65.5.0
3)安装 Python 包依赖项
#sudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 protobuf pybind11 cython pkgconfig packaging h5py==3.6.0
4)安装 Python 包依赖项
#sudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 protobuf pybind11 cython pkgconfig packaging h5py==3.6.0
5)确认CUDA已经被正常安装
#nvcc -V
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2019 NVIDIA Corporation
Built on Wed_Oct_23_21:14:42_PDT_2019
Cuda compilation tools, release 10.2, V10.2.89
6)安装TensorFlow
#sudo pip3 install --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v51 tensorflow==2.11.0+nv23.01
安装的 TensorFlow 版本必须与正在使用的 JetPack 版本一致，版本信息请查看官网文档。
7)验证安装
#python3
>>> import tensorflow
>>> import tensorflow as tf
2023-04-20 10:01:13.231340: I tensorflow/stream_executor/platform/default/dso_loader.cc:49] Successfully opened dynamic library libcudart.so.10.2
>>> print(tf.__version__)
2.11.0"""
]


generated_answer = """
根据提供的参考资料，以下是 Jetson Nano 安装 TensorFlow GPU 版本的完整步骤：

### 📦 安装准备
1. **硬件要求**：
   - 使用大容量高速 microSD 卡（建议 ≥64GB UHS-1）
   - 使用高品质 5V/2A 电源适配器
   - 推荐使用 NVIDIA AC8265 双模无线网卡（可选）
   - 确认设备型号：B02 版本有两路 CSI 相机接口

2. **系统要求**：
   - 已刷写官方 Jetson Nano 镜像
   - 确认 CUDA 环境已正确安装（JetPack 默认包含）
   - 通过 `nvcc -v` 验证 CUDA 版本（示例输出：`release 10.2, V10.2.89`）

---

### ⚙️ 安装 TensorFlow GPU 步骤
1. **安装系统依赖包**：
   ```bash
   sudo apt-get update
   sudo apt-get install libhdf5-serial-dev hdf5-tools libhdf5-dev \
   zlib1g-dev zip libjpeg9-dev liblapack-dev libblas-dev gfortran
   ```

2. **安装并升级 pip3**：
   ```bash
   sudo apt-get install python3-pip
   sudo python3 -m pip install --upgrade pip
   sudo pip3 install -U testresources setuptools==65.5.0
   ```

3. **安装 Python 依赖包**：
   ```bash
   sudo pip3 install -U numpy==1.22 future==0.19.2 mock==3.0.5 \
   keras_preprocessing==1.1.2 keras_applications==1.0.8 gast==0.4.0 \
   protobuf pybind11 cython pkgconfig packaging h5py==3.6.0
   ```

4. **安装 TensorFlow GPU 版本**：
   ```bash
   sudo pip3 install --extra-index-url \
   https://developer.download.nvidia.com/compute/redist/jp/v51 \
   tensorflow==2.11.0+nv23.01
   ```
   > 💡 **版本注意**：TensorFlow 版本必须与 JetPack 版本匹配

5. **验证安装**：
   ```bash
   python3 -c "import tensorflow as tf; print(tf.__version__)"
   ```
   ✅ 预期输出：`2.11.0` 及相关 CUDA 库加载信息

---
"""
all_scores = []
for i, reference in enumerate(knowledge_base):
    scores = evaluate_bertscore([generated_answer], [reference])
    all_scores.append({
        'index': i,
        'reference': reference,
        'scores': scores
    })

# 打印每个条目的 BERTScore
for score in all_scores:
    print(f"Knowledge Base Entry {score['index'] + 1}:")
    print(f"Reference: {score['reference'][:100]}...")  # 打印前100个字符
    print(f"BERTScore: {score['scores']}")
    print("-" * 80)