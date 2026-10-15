"""待候选人实现。避免读取dev_answers或题号/condition来构造答案。"""
import re

def prepare_messages(question, passages):
    """返回 [{"role":"system|user", "content":"..."}, ...]。
    passages仅含id/source/text，不包含答案或条件标记。
    必须请求JSON对象: {"answer": "简短答案", "citations": ["P..."]}。
    prompt需由本人设计、核查、解释。"""
    system = (
        "你是一个文档信息核验助手。你会收到一个问题和若干段带编号的资料。\n"
        "你的任务是只依据这些资料回答问题，并引用真正支撑答案的段落。\n"
        "必须严格返回一个 JSON 对象，不要输出任何其他文字或解释，格式如下：\n"
        '{"answer": "简短答案", "citations": ["段落ID"]}\n\n'
        "规则：\n"
        "1. 资料足够时，answer 填答案，citations 填语义上真正支撑该答案的段落 id。\n"
        "2. 如果问题要求一个数值（比例、百分比、差值、计数等），而资料里包含了计算所需的数字，请先计算再给出结果，不要因为“需要计算”就误判为证据不足。\n"
        "3. 只有当回答问题所必需的关键信息（如选择规则、候选数据）在资料中完全缺失、未提及时，answer 才填“证据不足”。如果资料里已经同时给出了“规则/判据”和“候选数据”，就必须应用规则得出结论，即使需要多步推理也不得用“证据不足”代替作答；此时 citations 填你实际用到的段落 id。仅当资料中确实缺少规则或缺少候选数据时，才可说“证据不足”。\n"
        "4. citations 中的 id 必须是资料里真实存在的 id，不得编造。\n"
        "5. 段落里出现相同关键词不等于支持你的结论，引用必须语义上真正证明答案。\n"
        "6. 不要使用资料以外的知识补充答案，不要把资料缺失的信息编造成事实。\n"
        "7. 当问题要求从多个候选中按规则选出唯一答案时，请在脑中逐步完成：① 列出规则中的全部条件；② 对每个候选逐条检查是否满足【每一个】条件；③ 淘汰任一条件不满足的候选；④ 若只剩一个则选它，若剩多个则按规则明确指定的比较指标（及其方向）选出。必须检查完全部条件，禁止只凭单一指标（如“支持率/覆盖率最高”）下结论。\n"
        "8. answer 只输出题目要求的答案本身（百分数、数值、编号、名称等），不要添加修饰词、解释或多余的文字。"
    )

    lines = [f"问题：{question}", "", "资料如下："]
    for p in passages:
        lines.append(f"[{p['id']}]（来源：{p['source']}）")
        lines.append(p['text'])
        lines.append("")
    lines.append("请只依据以上资料回答，并严格返回 JSON。")
    user = "\n".join(lines)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

def improve(question, passages):
    """返回重新组织/选择的原段落列表，不能修改id/source/text或使用答案标签。
    默认恒等映射仅用于联通，不算已完成改进。可自行扩展结构/调用，须披露与记录。"""
    # 相关性重排：按问题关键词(项目/版本/日期)与二字符片段在段落中的命中数降序排序，7 段全保留
    terms = re.findall(r'[一-鿿]{2}项目|R\d+|\d{4}-\d{2}', question)
    grams = {question[i:i+2] for i in range(len(question)-1)}
    def score(p):
        body = p['text']
        return sum(t in body for t in terms), sum(g in body for g in grams)
    return sorted(passages, key=score, reverse=True)
