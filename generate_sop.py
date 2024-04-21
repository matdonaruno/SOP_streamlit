import streamlit as st
import re
import openai

def generate_sop(main_title, subtitle, combined_text, revision_history_input):
    messages = [
        {
            "role": "system",
            "content":"""あなたは、臨床検査のSOPを生成する役立つアシスタントです。以下の項目に沿って詳細なSOPを作成してください：
            - MainTitle
            - SubTitle
            - 検査の目的
            - 測定法
            - 測定原理
            - パラメーター
            - 直進性
            - 正確性
            - 同時再現性
            - 定量下限
            - 機器間差
            - サンプルの種類
            - サンプルの貯法
            - 患者準備
            - 容器および添加剤の種類
            - 測定機器
            - 必要な機材および器具
            - 試薬および構成
            - 試薬の調整
            - 試薬保管条件および有効期限
            - サンプリング量
            - 必要量
            - 環境
            - 安全管理
            - 標準液の調整および保管条件
            - 検量線
            - 結果の判定
            - 校正の実施
            - トレーサビリティ
            - 操作ステップ
            - 精度管理試料の調整および保管条件
            - 内部精度管理
            - 精度管理許容限界
            - 外部精度管理
            - 干渉および交差反応
            - 分析結果の計算法
            - 測定の不確かさ
            - 不確かさの要因図
            - 結果が測定範囲外であった場合の定量結果決定に関する指示
            - 再検基準
            - 再検時のデータ選択基準
            - 警戒値・緊急異常値
            - 臨床的意義
            - 関連項目
            - 可能性のある変動要因
            各項目に必要な記述は省略せず、提供された情報に忠実な内容とします。各項目に関する情報を含めた詳細な且つ提供されたファイルをもとに正確なSOPを作成してください。各項目について、必要な情報、手順、注意点を具体的に説明してください。以下の情報を含むSOP（標準作業手順書）をMarkdown形式で生成してください。各項目にはタイトルを##で示し、必要な詳細情報を列挙してください。添付資料はSub Titleとします。各項目に必要な記述は省略せず提供されたファイルに忠実な内容とします。検査に用いられる手順の原理および測定法は提供資料の「測定原理」などが当てはまります。容器および添加剤の種類は空欄のままにします。操作ステップは簡潔ではなく、詳しくそのまま資料に忠実に記載します。干渉および交差反応はデータが表形式だったりしますが省略せず資料に忠実に出力します。結果計算法の原理・測定の不確かさを含むでは妨害物質・妨害薬剤の記載などがあてはまります。各項目に当てはまる記述がない場合は「該当なし」としてください。"""
        },
        {
            "role": "user",
            "content": f"Main Title: {main_title}, Subtitle: {subtitle}, Combined Text: {combined_text}"
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2048,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )
    sop_result = response.choices[0].message['content']

    pattern = {
        "検査の目的": r"## 検査の目的\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "測定法": r"## 測定法\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "測定原理": r"## 測定原理\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "パラメーター": r"## パラメーター\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "直進性": r"## 直進性\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "正確性": r"## 正確性\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "同時再現性": r"## 同時再現性\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "定量下限": r"## 定量下限\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "機器間差": r"## 機器間差\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "サンプルの種類": r"## サンプルの種類\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "サンプルの貯法": r"## サンプルの貯法\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "患者準備": r"## 患者準備\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "容器および添加剤の種類": r"## 容器および添加剤の種類\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "測定機器": r"## 測定機器\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "必要な機材および器具": r"## 必要な機材および器具\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "試薬および構成": r"## 試薬および構成\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "試薬の調整": r"## 試薬の調整\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "試薬保管条件および有効期限": r"## 試薬保管条件および有効期限\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "サンプリング量": r"## サンプリング量\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "必要量": r"## 必要量\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "環境": r"## 環境\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "安全管理": r"## 安全管理\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "標準液の調整および保管条件": r"## 標準液の調整および保管条件\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "検量線": r"## 検量線\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "結果の判定": r"## 結果の判定\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "校正の実施": r"## 校正の実施\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "トレーサビリティ": r"## トレーサビリティ\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "操作ステップ": r"## 操作ステップ\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "精度管理試料の調整および保管条件": r"## 精度管理試料の調整および保管条件\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "内部精度管理": r"## 内部精度管理\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "精度管理許容限界": r"## 精度管理許容限界\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "外部精度管理": r"## 外部精度管理\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "干渉および交差反応": r"## 干渉および交差反応\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "分析結果の計算法": r"## 分析結果の計算法\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "測定の不確かさ": r"## 測定の不確かさ\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "不確かさの要因図": r"## 不確かさの要因図\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "結果が測定範囲外であった場合の定量結果決定に関する指示": r"## 結果が測定範囲外であった場合の定量結果決定に関する指示\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "再検基準": r"## 再検基準\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "再検時のデータ選択基準": r"## 再検時のデータ選択基準\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "警戒値・緊急異常値": r"## 警戒値・緊急異常値\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "臨床的意義": r"## 臨床的意義\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "関連項目": r"## 関連項目\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "可能性のある変動要因": r"## 可能性のある変動要因\s*\n+(-*\s*(.+?))(?=\n## |\Z)"
    }

    revision_history = revision_history_input
    if not revision_history:
        revision_history = "改訂履歴が見つかりません"

    # 各セクションの内容を抽出して変数に格納し、先頭のハイフンを除去
    sections_content = {}
    for section, regex in pattern.items():
        match = re.search(regex, sop_result, re.DOTALL)
        if match:
            # マッチした内容を行ごとに分割し、各行の先頭からハイフンと空白を除去
            lines = match.group(1).split('\n')
            cleaned_lines = [line.lstrip('- ').strip() for line in lines]
            content = '\n'.join(cleaned_lines).strip()

            # 「記載なし」の場合、改訂履歴を追加しない
            if content == "記載なし" or content == "該当なし":
                sections_content[section] = "該当なし"

            else:
                if section == "参考資料":
                    # 改訂履歴を内容に含める
                    sections_content[section] = f"{content}\n({subtitle} {revision_history}"
                else:
                    sections_content[section] = f"{content}\n({subtitle} {revision_history})"
        else:
            sections_content[section] = "該当なし"

    # Streamlit UIにセクション内容を表示
    for section, content in sections_content.items():
        st.text_area(section, value=content)

    return sections_content


def generate_sop_for_selected_sections(main_title, subtitle, combined_text, revision_history_input, selected_sections):
    # 選択されたセクションに基づいてプロンプトを作成
    selected_sections_prompt = "\n- ".join([""] + selected_sections)
    system_message_content = f"""あなたは、臨床検査のSOPを生成する役立つアシスタントです。以下の選択された項目に沿って詳細なSOPを作成してください：{selected_sections_prompt}
    各項目に必要な情報、手順、注意点を具体的に説明してください。提供された情報に基づいて、詳細で正確なSOPを作成してください。"""

    messages = [
        {"role": "system", "content": system_message_content},
        {"role": "user", "content": f"Main Title: {main_title}, Sub Title: {subtitle}, Combined Text: {combined_text}"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2048,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )

    sop_result = response.choices[0].message['content']

    # 選択されたセクションの内容を抽出するための正規表現パターンを定義
    patterns = {section: r"## " + re.escape(section) + r"\s*\n+(-*\s*(.+?))(?=\n## |\Z)" for section in selected_sections}

    # 各セクションの内容を抽出してsections_contentに格納
    sections_content = {}
    for section, regex in patterns.items():
        match = re.search(regex, sop_result, re.DOTALL)
        if match:
            # マッチした内容を行ごとに分割し、各行の先頭からハイフンと空白を除去
            lines = match.group(1).split('\n')
            cleaned_lines = [line.lstrip('- ').strip() for line in lines]
            content = '\n'.join(cleaned_lines).strip()
            sections_content[section] = content if content else "該当なし"
        else:
            sections_content[section] = "該当なし"

    # Streamlit UIにセクション内容を表示（必要に応じて）
    for section, content in sections_content.items():
        st.text_area(section, value=content, height=100)

    return sections_content

def generate_dep_sop(section_title, combined_text):
    # システムメッセージにsection titleを含める
    system_prompt = f"あなたは、臨床検査のSOPを生成する役立つアシスタントです。次のセクションタイトル「{section_title}」に一致する詳細なSOPを作成してください。"
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"Combined Text: {combined_text}"
        }
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2048,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0
    )
    sop_result = response.choices[0].message['content']

    return sop_result
