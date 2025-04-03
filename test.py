# 原始 Unicode 转义字符串
data = {"objectives": "\u5b66\u751f\u80fd\u591f\u638c\u63e1Python\u7684\u57fa\u672c\u8bed\u6cd5\uff0c\u7406\u89e3\u53d8\u91cf\u3001\u6570\u636e\u7c7b\u578b\u3001\u63a7\u5236\u7ed3\u6784\u7b49\u6982\u5ff5\u3002", "plan_content": "# Python\u57fa\u7840\u8bed\u6cd5\u6559\u5b66\u8bbe\u8ba1\n\n## \u6559\u5b66\u76ee\u6807\n1. **\u77e5\u8bc6\u76ee\u6807**\uff1a\u638c\u63e1Python\u4e2d\u53d8\u91cf\u5b9a\u4e49\u4e0e\u4f7f\u7528\u7684\u57fa\u672c\u89c4\u5219\uff0c\u7406\u89e3\u6574\u6570\u3001\u6d6e\u70b9\u6570\u3001\u5b57\u7b26\u4e32\u7b49\u57fa\u672c\u6570\u636e\u7c7b\u578b\u7684\u7279\u70b9\u3002\n2. **\u6280\u80fd\u76ee\u6807**\uff1a\u80fd\u591f\u72ec\u7acb\u7f16\u5199\u5305\u542b\u6761\u4ef6\u5224\u65ad(if-else)\u548c\u5faa\u73af(for/while)\u7ed3\u6784\u7684\u7b80\u5355Python\u7a0b\u5e8f\u3002\n3. **\u5e94\u7528\u76ee\u6807**\uff1a\u901a\u8fc7\u89e3\u51b3\u5b9e\u9645\u95ee\u9898\uff0c\u57f9\u517b\u5b66\u751f\u8fd0\u7528Python\u57fa\u7840\u8bed\u6cd5\u8fdb\u884c\u7b80\u5355\u7f16\u7a0b\u7684\u80fd\u529b\u3002\n4. **\u601d\u7ef4\u76ee\u6807**\uff1a\u57f9\u517b\u8ba1\u7b97\u601d\u7ef4\uff0c\u7406\u89e3\u7a0b\u5e8f\u6d41\u7a0b\u63a7\u5236\u7684\u57fa\u672c\u903b\u8f91\u7ed3\u6784\u3002\n\n## \u6559\u5b66\u91cd\u96be\u70b9\n**\u91cd\u70b9**\uff1a\n- \u53d8\u91cf\u7684\u547d\u540d\u89c4\u5219\u4e0e\u4f7f\u7528\n- \u57fa\u672c\u6570\u636e\u7c7b\u578b\u7684\u533a\u522b\u4e0e\u5e94\u7528\u573a\u666f\n- \u6761\u4ef6\u8bed\u53e5\u548c\u5faa\u73af\u8bed\u53e5\u7684\u8bed\u6cd5\u7ed3\u6784\n\n**\u96be\u70b9**\uff1a\n- \u6761\u4ef6\u8bed\u53e5\u7684\u5d4c\u5957\u4f7f\u7528\n- \u5faa\u73af\u7ed3\u6784\u7684\u63a7\u5236(break/continue)\n- \u4e0d\u540c\u6570\u636e\u7c7b\u578b\u95f4\u7684\u8f6c\u6362\n\n**\u7a81\u7834\u7b56\u7565**\uff1a\n- \u4f7f\u7528\u7c7b\u6bd4\u6cd5\u8bb2\u89e3\u53d8\u91cf\u6982\u5ff5(\u5982\u53d8\u91cf\u662f\u5b58\u50a8\u6570\u636e\u7684\"\u76d2\u5b50\")\n- \u901a\u8fc7\u53ef\u89c6\u5316\u6d41\u7a0b\u56fe\u5c55\u793a\u7a0b\u5e8f\u6267\u884c\u8fc7\u7a0b\n- \u8bbe\u8ba1\u6e10\u8fdb\u5f0f\u7ec3\u4e60\u9898\u76ee\uff0c\u4ece\u7b80\u5355\u5230\u590d\u6742\n\n## \u6559\u5b66\u5185\u5bb9\n1. **Python\u57fa\u7840\u6982\u5ff5**\n   - Python\u8bed\u8a00\u7b80\u4ecb\n   - \u5f00\u53d1\u73af\u5883\u914d\u7f6e\n\n2. **\u53d8\u91cf\u4e0e\u6570\u636e\u7c7b\u578b**\n   - \u53d8\u91cf\u7684\u5b9a\u4e49\u4e0e\u547d\u540d\u89c4\u5219\n   - \u57fa\u672c\u6570\u636e\u7c7b\u578b\uff1a\n     * \u6574\u6570(int)\n     * \u6d6e\u70b9\u6570(float)\n     * \u5b57\u7b26\u4e32(str)\n     * \u5e03\u5c14\u503c(bool)\n   - \u7c7b\u578b\u8f6c\u6362\u65b9\u6cd5\n\n3. **\u7a0b\u5e8f\u63a7\u5236\u7ed3\u6784**\n   - \u6761\u4ef6\u8bed\u53e5\uff1a\n     * if\u8bed\u53e5\n     * if-else\u8bed\u53e5\n     * if-elif-else\u8bed\u53e5\n   - \u5faa\u73af\u8bed\u53e5\uff1a\n     * for\u5faa\u73af\n     * while\u5faa\u73af\n     * \u5faa\u73af\u63a7\u5236\u8bed\u53e5(break/continue)\n\n4. **\u7efc\u5408\u5e94\u7528**\n   - \u7b80\u5355\u8ba1\u7b97\u5668\u5b9e\u73b0\n   - \u6210\u7ee9\u7b49\u7ea7\u5224\u65ad\n   - \u6570\u5b57\u731c\u8c1c\u6e38\u620f\n\n## \u6559\u5b66\u65f6\u95f4\u5b89\u6392(45\u5206\u949f)\n| \u6559\u5b66\u73af\u8282 | \u65f6\u95f4\u5206\u914d |\n|---------|---------|\n| \u5bfc\u5165\u65b0\u8bfe | 5\u5206\u949f |\n| \u53d8\u91cf\u4e0e\u6570\u636e\u7c7b\u578b\u8bb2\u89e3 | 10\u5206\u949f |\n| \u4e92\u52a8\u7ec3\u4e601 | 5\u5206\u949f |\n| \u6761\u4ef6\u8bed\u53e5\u8bb2\u89e3 | 8\u5206\u949f |\n| \u4e92\u52a8\u7ec3\u4e602 | 5\u5206\u949f |\n| \u5faa\u73af\u8bed\u53e5\u8bb2\u89e3 | 7\u5206\u949f |\n| \u4e92\u52a8\u7ec3\u4e603 | 3\u5206\u949f |\n| \u8bfe\u5802\u5c0f\u7ed3 | 2\u5206\u949f |\n\n## \u6559\u5b66\u8fc7\u7a0b\n\n### 1. \u5bfc\u5165\u65b0\u8bfe(5\u5206\u949f)\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u60c5\u5883\u5bfc\u5165\u6cd5  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n- \u5c55\u793a\u4e00\u4e2a\u7b80\u5355\u7684Python\u7a0b\u5e8f(\u5982\u6253\u5370\"Hello World\"\u548c\u7b80\u5355\u8ba1\u7b97)\n- \u8be2\u95ee\u5b66\u751f\u65e5\u5e38\u751f\u6d3b\u4e2d\u54ea\u4e9b\u573a\u666f\u53ef\u4ee5\u7528\u7a0b\u5e8f\u81ea\u52a8\u5316\u5904\u7406\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u6f14\u793a\u7a0b\u5e8f\uff0c\u63d0\u51fa\u95ee\u9898\u5f15\u5bfc\u601d\u8003\n- \u5b66\u751f\uff1a\u89c2\u5bdf\u7a0b\u5e8f\u8fd0\u884c\u7ed3\u679c\uff0c\u601d\u8003\u5e76\u56de\u7b54\u95ee\u9898\n\n**\u5de5\u5177\u6750\u6599**\uff1aPython IDLE\u6216Jupyter Notebook\u6f14\u793a  \n**\u9884\u671f\u6210\u679c**\uff1a\u6fc0\u53d1\u5b66\u4e60\u5174\u8da3\uff0c\u5efa\u7acbPython\u4e0e\u5b9e\u9645\u751f\u6d3b\u7684\u8054\u7cfb\n\n### 2. \u53d8\u91cf\u4e0e\u6570\u636e\u7c7b\u578b\u8bb2\u89e3(10\u5206\u949f)\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u8bb2\u89e3\u6f14\u793a\u6cd5  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n1. \u8bb2\u89e3\u53d8\u91cf\u7684\u6982\u5ff5\u548c\u547d\u540d\u89c4\u5219\n2. \u6f14\u793a\u4e0d\u540c\u7c7b\u578b\u53d8\u91cf\u7684\u5b9a\u4e49\u548c\u4f7f\u7528\n3. \u5c55\u793a\u7c7b\u578b\u8f6c\u6362\u7684\u65b9\u6cd5\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u9010\u6b65\u8bb2\u89e3\u5e76\u6f14\u793a\u4ee3\u7801\n- \u5b66\u751f\uff1a\u8ddf\u968f\u6559\u5e08\u64cd\u4f5c\uff0c\u8bb0\u5f55\u5173\u952e\u70b9\n\n**\u5de5\u5177\u6750\u6599**\uff1a\u6295\u5f71\u4eea\u3001\u793a\u4f8b\u4ee3\u7801  \n**\u5173\u952e\u4ee3\u7801\u793a\u4f8b**\uff1a\n```python\nname = \"\u5f20\u4e09\"  # \u5b57\u7b26\u4e32\nage = 18      # \u6574\u6570\nheight = 1.75 # \u6d6e\u70b9\u6570\nis_student = True  # \u5e03\u5c14\u503c\n\n# \u7c7b\u578b\u8f6c\u6362\nnum_str = \"123\"\nnum_int = int(num_str)\n```\n\n### 3. \u4e92\u52a8\u7ec3\u4e601(5\u5206\u949f) \u2605\u4e92\u52a8\u73af\u8282\u2605\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u5c0f\u7ec4\u7ade\u8d5b  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n- \u5c06\u5b66\u751f\u5206\u62103-4\u4eba\u5c0f\u7ec4\n- \u6bcf\u7ec4\u57283\u5206\u949f\u5185\u5199\u51fa\u5c3d\u53ef\u80fd\u591a\u7684\u5408\u6cd5\u53d8\u91cf\u540d\n- \u7136\u540e\u4e92\u76f8\u68c0\u67e5\u53d8\u91cf\u540d\u662f\u5426\u7b26\u5408\u89c4\u5219\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u5ba3\u5e03\u89c4\u5219\uff0c\u8ba1\u65f6\u5e76\u8bc4\u5224\n- \u5b66\u751f\uff1a\u5c0f\u7ec4\u5408\u4f5c\uff0c\u79ef\u6781\u601d\u8003\n\n**\u9884\u671f\u6210\u679c**\uff1a\u5de9\u56fa\u53d8\u91cf\u547d\u540d\u89c4\u5219\uff0c\u57f9\u517b\u56e2\u961f\u534f\u4f5c\u80fd\u529b\n\n### 4. \u6761\u4ef6\u8bed\u53e5\u8bb2\u89e3(8\u5206\u949f)\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u793a\u4f8b\u5206\u6790\u6cd5  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n1. \u8bb2\u89e3if\u8bed\u53e5\u7684\u57fa\u672c\u7ed3\u6784\n2. \u6f14\u793aif-else\u548cif-elif-else\u7684\u4f7f\u7528\n3. \u5c55\u793a\u6761\u4ef6\u8868\u8fbe\u5f0f\u7684\u591a\u79cd\u5199\u6cd5\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u7528\u6d41\u7a0b\u56fe\u8f85\u52a9\u8bb2\u89e3\u6761\u4ef6\u5224\u65ad\u903b\u8f91\n- \u5b66\u751f\uff1a\u7406\u89e3\u4e0d\u540c\u6761\u4ef6\u4e0b\u7684\u7a0b\u5e8f\u8d70\u5411\n\n**\u5173\u952e\u4ee3\u7801\u793a\u4f8b**\uff1a\n```python\nscore = 85\nif score >= 90:\n    print(\"\u4f18\u79c0\")\nelif score >= 80:\n    print(\"\u826f\u597d\") \nelse:\n    print(\"\u7ee7\u7eed\u52aa\u529b\")\n```\n\n### 5. \u4e92\u52a8\u7ec3\u4e602(5\u5206\u949f) \u2605\u4e92\u52a8\u73af\u8282\u2605\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u89d2\u8272\u626e\u6f14  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n- \u8bbe\u8ba1\"\u4ea4\u901a\u4fe1\u53f7\u706f\"\u60c5\u666f\n- \u5b66\u751f\u5206\u522b\u626e\u6f14\u7ea2\u706f\u3001\u7eff\u706f\u548c\u9ec4\u706f\n- \u6839\u636e\u6559\u5e08\u7ed9\u51fa\u7684\u4fe1\u53f7\u706f\u989c\u8272\uff0c\u76f8\u5e94\"\u706f\"\u8981\u8bf4\u51fa\u6b63\u786e\u7684\u884c\u52a8\u6307\u793a\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u7ec4\u7ec7\u6d3b\u52a8\uff0c\u7ed9\u51fa\u4fe1\u53f7\u6307\u793a\n- \u5b66\u751f\uff1a\u6839\u636e\u89d2\u8272\u505a\u51fa\u53cd\u5e94\n\n**\u9884\u671f\u6210\u679c**\uff1a\u5f62\u8c61\u7406\u89e3\u6761\u4ef6\u5224\u65ad\u7684\u6267\u884c\u8fc7\u7a0b\n\n### 6. \u5faa\u73af\u8bed\u53e5\u8bb2\u89e3(7\u5206\u949f)\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u5bf9\u6bd4\u8bb2\u89e3\u6cd5  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n1. \u5bf9\u6bd4for\u548cwhile\u5faa\u73af\u7684\u9002\u7528\u573a\u666f\n2. \u6f14\u793arange()\u51fd\u6570\u7684\u4f7f\u7528\n3. \u8bb2\u89e3\u5faa\u73af\u63a7\u5236\u8bed\u53e5break\u548ccontinue\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u901a\u8fc7\u5b9e\u4f8b\u5c55\u793a\u5faa\u73af\u6267\u884c\u8fc7\u7a0b\n- \u5b66\u751f\uff1a\u89c2\u5bdf\u5faa\u73af\u53d8\u91cf\u7684\u53d8\u5316\n\n**\u5173\u952e\u4ee3\u7801\u793a\u4f8b**\uff1a\n```python\n# for\u5faa\u73af\u793a\u4f8b\nfor i in range(5):\n    print(i)\n\n# while\u5faa\u73af\u793a\u4f8b\ncount = 0\nwhile count < 5:\n    print(count)\n    count += 1\n```\n\n### 7. \u4e92\u52a8\u7ec3\u4e603(3\u5206\u949f) \u2605\u4e92\u52a8\u73af\u8282\u2605\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u5feb\u901f\u95ee\u7b54  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n- \u6559\u5e08\u63d0\u51fa\u5173\u4e8e\u5faa\u73af\u7684\u5feb\u901f\u5224\u65ad\u9898\n- \u5b66\u751f\u901a\u8fc7\u4e3e\u624b\u6216\u7ad9\u7acb\u65b9\u5f0f\u8868\u793a\u5bf9\u9519\n\n**\u793a\u4f8b\u95ee\u9898**\uff1a\n1. \"for\u5faa\u73af\u9002\u5408\u5728\u672a\u77e5\u5faa\u73af\u6b21\u6570\u65f6\u4f7f\u7528\"(\u9519)\n2. \"break\u8bed\u53e5\u53ef\u4ee5\u8df3\u51fa\u5f53\u524d\u5faa\u73af\"(\u5bf9)\n\n**\u9884\u671f\u6210\u679c**\uff1a\u5373\u65f6\u68c0\u6d4b\u5bf9\u5faa\u73af\u6982\u5ff5\u7684\u7406\u89e3\n\n### 8. \u8bfe\u5802\u5c0f\u7ed3(2\u5206\u949f)\n**\u6559\u5b66\u65b9\u6cd5**\uff1a\u601d\u7ef4\u5bfc\u56fe\u603b\u7ed3  \n**\u6d3b\u52a8\u5b89\u6392**\uff1a\n- \u6559\u5e08\u7528\u601d\u7ef4\u5bfc\u56fe\u56de\u987e\u672c\u8282\u8bfe\u91cd\u70b9\n- \u5f3a\u8c03\u6613\u9519\u70b9\u548c\u6ce8\u610f\u4e8b\u9879\n\n**\u5e08\u751f\u884c\u4e3a**\uff1a\n- \u6559\u5e08\uff1a\u7cfb\u7edf\u5f52\u7eb3\u77e5\u8bc6\u70b9\n- \u5b66\u751f\uff1a\u67e5\u6f0f\u8865\u7f3a\uff0c\u63d0\u51fa\u95ee\u9898\n\n## \u8bfe\u540e\u4f5c\u4e1a\n**\u57fa\u7840\u9898**\uff1a\n1. \u7f16\u5199\u7a0b\u5e8f\u8ba1\u7b971-100\u6240\u6709\u5076\u6570\u7684\u548c\n2. \u5b9e\u73b0\u4e00\u4e2a\u7b80\u5355\u7684\u7528\u6237\u767b\u5f55\u9a8c\u8bc1(\u9884\u8bbe\u7528\u6237\u540d\u548c\u5bc6\u7801)\n\n**\u62d3\u5c55\u9898**\uff1a\n1. \u7f16\u5199\u731c\u6570\u5b57\u6e38\u620f\u7a0b\u5e8f(\u8ba1\u7b97\u673a\u968f\u673a\u751f\u6210\u6570\u5b57\uff0c\u7528\u6237\u731c\u6d4b)\n2. \u5b9e\u73b0\u4e00\u4e2a\u7b80\u6613\u8ba1\u7b97\u5668\uff0c\u652f\u6301\u52a0\u51cf\u4e58\u9664\u8fd0\u7b97\n\n**\u6311\u6218\u9898**\uff1a\n\u4f7f\u7528\u5faa\u73af\u7ed3\u6784\u6253\u5370\u5982\u4e0b\u56fe\u6848\uff1a\n```\n    *\n   ***\n  *****\n *******\n```", "analysis": "\u6839\u636e\u63d0\u4f9b\u7684\u9884\u4e60\u7b54\u9898\u53cd\u9988\uff0c\u6240\u6709\u5b66\u751f\u90fd\u6b63\u786e\u56de\u7b54\u4e86\u4e00\u9053\u5173\u4e8e\u5e94\u7528\u5c42\u534f\u8bae\u7684\u9009\u62e9\u9898\uff0c\u6b63\u786e\u7387\u4e3a100%\u3002\u8fd9\u8868\u660e\u5b66\u751f\u5728\u8fd9\u4e00\u77e5\u8bc6\u70b9\u4e0a\u7684\u638c\u63e1\u60c5\u51b5\u975e\u5e38\u826f\u597d\u3002"}

# 直接解码 Unicode 转义字符
decoded_objectives = data['analysis'].encode('utf-8').decode('utf-8')

# 或者使用 json.loads() 来解码
# decoded_objectives = json.loads(f'"{objectives}"')

print(decoded_objectives)