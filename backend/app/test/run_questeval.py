from questeval.questeval_metric import QuestEval

questeval = QuestEval(task="text2text")  # 或"qa"模式

def check_consistency(generated_text, knowledge_context):
    score = questeval.compute(
        sources=[knowledge_context],
        predictions=[generated_text]
    )['f1']  # 使用F1值综合判断
    return score > 0.6  # 可调整阈值


history_fact ="""
1.张量(Tensor)
TensorFlow.js 中的中心数据单元是张量（tensor）：一维或多维数组。一个 Tensor 实例的 shape 属性定义了其数组形状。
Tensor 主要构造函数是 tf.tensor 函数：
// 2x3 Tensor
const shape = [2, 3]; // 2 rows, 3 columns
const a = tf.tensor([1.0, 2.0, 3.0, 10.0, 20.0, 30.0], shape);
a.print(); // print Tensor values
// Output: [[1 , 2 , 3 ],
//          [10, 20, 30]]

// The shape can also be inferred:
const b = tf.tensor([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]]);
b.print();
// Output: [[1 , 2 , 3 ],
//          [10, 20, 30]]
"""
generated_desc = """
### **张量的核心定义**
1. **多维数据容器**
   - 机器学习数据的标准存储形式（标量、向量、矩阵、高维数组）
   - 示例（两种创建方式）：
     ```javascript
     // 显式定义形状（2行3列）
     const a = tf.tensor([1.0, 2.0, 3.0, 10.0, 20.0, 30.0], [2, 3]);
     a.print();
     // 输出: [[1, 2, 3], [10, 20, 30]]

     // 隐式推断形状（自动识别为2x3矩阵）
     const b = tf.tensor([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]]);
     b.print();
     // 输出: [[1, 2, 3], [10, 20, 30]]
     ```
"""
is_consistent = check_consistency(generated_desc, history_fact)
