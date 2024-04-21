import streamlit as st
import openai
import re
from io import BytesIO
import os
from dotenv import load_dotenv
import tempfile
from utils import extract_text, display_pdf_as_images, extract_revision_history
from database_operations_sql import save_sop_to_database, Session, UploadedFile, SOPDetail, edit_sop_details, fetch_sop_list, save_new_facility_name_if_not_exists, fetch_facility_names_from_database, fetch_facility_id_by_name
from additional_sop import addSOPfile
from gpts import ask_gpt, fetch_sop_by_facility
from streamlit_option_menu import option_menu
from output import output_csv, fetch_facilities
from mysop_discriptions import show_sop_descriptions



load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")
#st.title('SOP Creation with GPT-3.5 Turbo🌏')


def generate_sop(main_title, subtitle, combined_text, revision_history_input):
    messages = [
        {
            "role": "system",
            "content": "あなたは、臨床検査の検査項目に対するSOPを生成する役立つアシスタントです。以下の項目に沿って、検査の目的、検査に用いられる手順の原理および測定法、性能特性、サンプルの種類、患者の準備、容器および添加剤の種類、必要な機材および試薬、環境および安全管理、校正手順（計量計測トレーサビリティ）、操作ステップ、精度管理手順、干渉および交差反応、結果計算法の原理・測定の不確かさを含む、生物学的基準範囲または臨床判断値、検査結果の報告範囲、結果が測定範囲外であった場合の定量結果決定に関する指示、再検査実施手順、警戒値・緊急異常値、検査室の臨床的解釈、可能性のある変動要因、参考資料に関する情報を含めた詳細な且つ提供されたファイルをもとに正確なSOPを作成してください。それぞれの項目について、必要な情報、手順、注意点を具体的に説明してください。以下の情報を含むSOP（標準作業手順書）をMarkdown形式で生成してください。各項目にはタイトルを##で示し、必要な詳細情報を列挙してください。添付資料はSub Titleとします。各項目に必要な記述は省略せず提供されたファイルに忠実な内容とします。検査に用いられる手順の原理および測定法は提供資料の「測定原理」などが当てはまります。容器および添加剤の種類は空欄のままにします。操作ステップは簡潔ではなく、詳しくそのまま資料に忠実に記載します。干渉および交差反応はデータが表形式だったりしますが省略せず資料に忠実に出力します。結果計算法の原理・測定の不確かさを含むでは妨害物質・妨害薬剤の記載などがあてはまります。各項目に当てはまる記述がない場合は「該当なし」としてください。"
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
        "検査に用いられる手順の原理および測定法": r"## 検査に用いられる手順の原理および測定法\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "性能特性": r"## 性能特性\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "サンプルの種類": r"## サンプルの種類\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "患者の準備": r"## 患者準備\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "容器および添加剤の種類": r"## 容器および添加剤の種類\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "必要な機材および試薬": r"## 必要な機材および試薬\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "環境および安全管理": r"## 環境および安全管理\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "校正手順（計量計測トレーサビリティ）": r"## 校正手順（計量計測トレーサビリティ）\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "操作ステップ": r"## 操作ステップ\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "精度管理手順": r"## 精度管理手順\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "干渉および交差反応": r"## 干渉および交差反応\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "結果計算法の原理・測定の不確かさを含む": r"## 結果計算法の原理・測定の不確かさを含む\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "生物学的基準範囲または臨床判断値": r"## 生物学的基準範囲または臨床判断値\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "検査結果の報告範囲、結果が測定範囲外であった場合の定量結果決定に関する指示": r"## 検査結果の報告範囲、結果が測定範囲外であった場合の定量結果決定に関する指示\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "再検査実施手順": r"## 再検査実施手順\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "警戒値・緊急異常値": r"## 警戒値・緊急異常値\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "検査室の臨床的解釈": r"## 検査室の臨床的解釈\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "可能性のある変動要因": r"## 可能性のある変動要因\s*\n+(-*\s*(.+?))(?=\n## |\Z)",
        "参考資料": r"## 参考資料\s*\n+(-*\s*(.+?))(?=\n## |\Z)"
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

def display_sop_list_for_editing():
    session = Session()
    sop_list = fetch_sop_list(session)
    session.close()

    sop_options = [(sop.id, sop.main_title) for sop in sop_list]
    sop_option_ids, sop_option_titles = zip(*sop_options)  # Unzip to separate ids and titles for the selectbox

    sop_id = st.selectbox("Select SOP to edit", options=sop_option_ids, format_func=lambda x: sop_option_titles[sop_option_ids.index(x)])
    return sop_id

def display_sop_edit_form(sop_id):
    session = Session()
    sop_detail = session.query(SOPDetail).filter(SOPDetail.id == sop_id).first()
    submitted = False
    facility_names = fetch_facility_names_from_database()

    if sop_detail:
        selected_facility_name = st.selectbox(
            "Facility Name",
            options=facility_names + ["その他（新しい施設名を入力）"],
            index=0,  # 初期値を設定
            key=f"facility_name_{sop_id}"
        )

        # 「その他」が選択された場合にのみ新しい施設名を入力するフィールドを表示
        new_facility_name = ""
        if selected_facility_name == "その他（新しい施設名を入力）":
            new_facility_name = st.text_input("New Facility Name", key=f"new_facility_name_{sop_id}")



    st.text_input("Main Title", value=sop_detail.main_title, key=f"main_title_{sop_id}")
    st.text_input("Sub Title", value=sop_detail.subtitle, key=f"subtitle_{sop_id}")
    st.text_area("Revision History", value=sop_detail.revision_history, key=f"revision_history_{sop_id}")
    st.text_area("Purpose", value=sop_detail.purpose, key=f"purpose_{sop_id}")
    st.text_area("Procedure Principle", value=sop_detail.procedure_principle, key=f"procedure_principle_{sop_id}")
    st.text_area("Performance Characteristics", value=sop_detail.performance_characteristics, key=f"performance_characteristics_{sop_id}")
    st.text_area("Sample Type", value=sop_detail.sample_type, key=f"sample_type_{sop_id}")
    st.text_area("Patient Preparation", value=sop_detail.patient_preparation, key=f"patient_preparation_{sop_id}")
    st.text_area("Container and Additives", value=sop_detail.container, key=f"container_{sop_id}")
    st.text_area("Equipment and Reagents", value=sop_detail.equipment_and_reagents, key=f"equipment_and_reagents_{sop_id}")
    st.text_area("Environmental and Safety Management", value=sop_detail.environmental_and_safety_management, key=f"environmental_and_safety_management_{sop_id}")
    st.text_area("Calibration Procedure", value=sop_detail.calibration_procedure, key=f"calibration_procedure_{sop_id}")
    st.text_area("Operation Steps", value=sop_detail.operation_steps, key=f"operation_steps_{sop_id}")
    st.text_area("Accuracy Control Procedures", value=sop_detail.accuracy_control_procedures, key=f"accuracy_control_procedures_{sop_id}")
    st.text_area("Interference and Cross Reactivity", value=sop_detail.interference_and_cross_reactivity, key=f"interference_and_cross_reactivity_{sop_id}")
    st.text_area("Result Calculation Principle", value=sop_detail.result_calculation_principle, key=f"result_calculation_principle_{sop_id}")
    st.text_area("Biological Reference Range", value=sop_detail.biological_reference_range, key=f"biological_reference_range_{sop_id}")
    st.text_area("Instructions for Out of Range Results", value=sop_detail.instructions_for_out_of_range_results, key=f"instructions_for_out_of_range_results_{sop_id}")
    st.text_area("Reinspection Procedure", value=sop_detail.reinspection_procedure, key=f"reinspection_procedure_{sop_id}")
    st.text_area("Alert Values", value=sop_detail.alert_values, key=f"alert_values_{sop_id}")
    st.text_area("Clinical Interpretation", value=sop_detail.clinical_interpretation, key=f"clinical_interpretation_{sop_id}")
    st.text_area("Possible Variability Factors", value=sop_detail.possible_variability_factors, key=f"possible_variability_factors_{sop_id}")
    st.text_area("References", value=sop_detail.references, key=f"references_{sop_id}")
    
    st.text_input("Creator/Editor", key=f"creator_editor_{sop_id}")
    st.text_input("Approver", key=f"approver_{sop_id}")
    st.text_input("Document Manager", key=f"document_manager_{sop_id}")
    st.text_area("Own Revision History", key=f"own_revision_history_{sop_id}")

    submitted = st.button("Finish Editing and Save Changes")

    session.close()
    return submitted, selected_facility_name, new_facility_name

def show_home_section():
    
    st.title('Welcome to the SOP Manager')
    st.write('This is the home page of the SOP management application. From here, you can navigate to other sections using the menu on the left.Choose "Create New SOP" to add a new Standard Operating Procedure, or select "Edit SOP" to modify an existing one.')
    st.write('(SOP管理アプリケーションのホームページへようこそ。ここでは、左側のメニューを使用して他のセクションへのナビゲーションが可能です。「Create New SOP」を選択して新しい標準作業手順書を追加するか、「Edit SOP」を選択して既存のものを編集してください。)')

def show_ask_gpt_section():
    st.title("AI Answers Your SOP Questions")
    st.info("""
    **注意**: SOPの内容に関して質問する場合は、返答の後に「この返答はどのSOPからのものか？」を必ず確認してください。
    """)

    # "messages"キーがst.session_stateに存在しない場合、空のリストで初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 初期メッセージがまだ追加されていない場合、追加する
    if "init_message" not in st.session_state:
        st.session_state.messages.append({"role": "system", "content": "Hello 👋, 何かお手伝いできることはありますか？"})
        # 初期メッセージが追加されたことを記録
        st.session_state.init_message = True

    facilities = fetch_facilities()
    facility_names = [facility.name for facility in facilities]
    selected_facility = st.selectbox("Select Facility", facility_names)

    if selected_facility:
        sop_content = fetch_sop_by_facility(selected_facility)

        question = st.chat_input("質問を入力してください。")
        if question:
            # ユーザーの質問を履歴に追加
            st.session_state.messages.append({"role": "user", "content": question})

            # GPTに質問して回答を取得
            answer = ask_gpt(sop_content, question)
            # GPTの回答を履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # チャット履歴を表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])



def main():
    print("main 関数の開始")
    
    # サイドバーでのメニュー選択
    with st.sidebar:
        selected = option_menu("Main Menu", ["Home", "Create New SOP", "Edit SOP", "Additional SOPs", "My SOP Discriptions", "Output CSV", "AI Answers Your SOP Lists"], icons=["house", "file-earmark-pdf", "pencil", "file-earmark-plus-fill", "file-text", "cloud-download", "robot"], menu_icon="cast", default_index=0)

    # メニュー選択に基づいてアクションを実行
    if selected == "Home":
        show_home_section()
    elif selected == "Create New SOP":
        show_create_sop_section()
    elif selected == "Edit SOP":
        show_edit_sop_section()


        if 'selected_sop_id_for_editing' in st.session_state and st.session_state.selected_sop_id_for_editing:
            sop_id = st.session_state.selected_sop_id_for_editing
            submitted, selected_facility_name, new_facility_name = display_sop_edit_form(sop_id)

            if submitted:
                # 新しい施設名が入力されたかどうかを確認
                if selected_facility_name == "その他（新しい施設名を入力）" and new_facility_name:
                    facility_id = save_new_facility_name_if_not_exists(new_facility_name)
                else:
                    facility_id = fetch_facility_id_by_name(selected_facility_name)  # 既存の施設名から施設IDを取得する関数

                success, message = edit_sop_details(
                    sop_id=sop_id,
                    main_title=st.session_state[f"main_title_{sop_id}"],
                    subtitle=st.session_state[f"subtitle_{sop_id}"],
                    revision_history=st.session_state[f"revision_history_{sop_id}"],
                    purpose=st.session_state[f"purpose_{sop_id}"],
                    procedure_principle=st.session_state[f"procedure_principle_{sop_id}"],
                    performance_characteristics=st.session_state[f"performance_characteristics_{sop_id}"],
                    sample_type=st.session_state[f"sample_type_{sop_id}"],
                    patient_preparation=st.session_state[f"patient_preparation_{sop_id}"],
                    container=st.session_state[f"container_{sop_id}"],
                    equipment_and_reagents=st.session_state[f"equipment_and_reagents_{sop_id}"],
                    environmental_and_safety_management=st.session_state[f"environmental_and_safety_management_{sop_id}"],
                    calibration_procedure=st.session_state[f"calibration_procedure_{sop_id}"],
                    operation_steps=st.session_state[f"operation_steps_{sop_id}"],
                    accuracy_control_procedures=st.session_state[f"accuracy_control_procedures_{sop_id}"],
                    interference_and_cross_reactivity=st.session_state[f"interference_and_cross_reactivity_{sop_id}"],
                    result_calculation_principle=st.session_state[f"result_calculation_principle_{sop_id}"],
                    biological_reference_range=st.session_state[f"biological_reference_range_{sop_id}"],
                    instructions_for_out_of_range_results=st.session_state[f"instructions_for_out_of_range_results_{sop_id}"],
                    reinspection_procedure=st.session_state[f"reinspection_procedure_{sop_id}"],
                    alert_values=st.session_state[f"alert_values_{sop_id}"],
                    clinical_interpretation=st.session_state[f"clinical_interpretation_{sop_id}"],
                    possible_variability_factors=st.session_state[f"possible_variability_factors_{sop_id}"],
                    references=st.session_state[f"references_{sop_id}"],
                    facility_id=facility_id,
                    creator_editor=st.session_state[f"creator_editor_{sop_id}"],
                    approver=st.session_state[f"approver_{sop_id}"],
                    document_manager=st.session_state[f"document_manager_{sop_id}"],
                    own_revision_history=st.session_state[f"own_revision_history_{sop_id}"]
                    )

                if success:
                    st.success("SOP details updated successfully.")
                    if st.button('Edit New SOP'):
                        st.experimental_rerun()
                else:
                    st.error(f"Failed to update SOP details: {message}")
        else:
            st.info("Please select an SOP to edit.")

    elif selected == "Additional SOPs":
        addSOPfile()

    elif selected == "My SOP Discriptions":

        st.title("My SOP Discriptions")
        selected_facility_name = st.selectbox(
        'Select Facility',
        options=fetch_facility_names_from_database(),  # データベースから施設名のリストを取得
        index=0  # デフォルトで最初のオプションを選択
        )

        if st.button("Show SOPs"):
            df = show_sop_descriptions(selected_facility_name)
            st.write(f"SOPs for {selected_facility_name}:")
            st.dataframe(df, width=500)
            
            if st.button("Back"):
                st.experimental_rerun()

    elif selected == "Output CSV":
        output_csv()
    elif selected == "AI Answers Your SOP Lists":
        show_ask_gpt_section()

    else:
        st.header("Welcome to the SOP Manager")
        st.write("Please select an option from the menu.")

def show_create_sop_section():
        st.title('SOP Creation with GPT-3.5 Turbo🌏')
        st.write("このページでは検査項目の添付文書から項目SOPのベースとなるものを作成します。")
        st.write("作成する項目のメインとなる添付文書のPFDを使用してください。")
        main_title = st.text_input('Enter Main Title (SOP項目名):')
        subtitle = st.text_input("Enter Sub Title （SOP 使用試薬名）:")
        uploaded_files = st.file_uploader("Upload SOP-related files", accept_multiple_files=True, type=['pdf', 'txt'])

        if 'sop_generated' not in st.session_state:
            st.session_state.sop_generated = False

        if uploaded_files and main_title and subtitle:
            combined_text = ""
            revision_history_input = ""
            revision_histories = []

            col1, col2 = st.columns([1, 2])  # 画面を左右2つのカラムに分割

            with col1:
                st.subheader("Uploaded Files and Previews")
                for uploaded_file in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        display_pdf_as_images(tmp_file.name, subtitle)  # Display PDF as images with subtitle
                        os.unlink(tmp_file.name)

                    file_text = extract_text(BytesIO(uploaded_file.getvalue()), uploaded_file.type)
                    combined_text += "\n\n" + file_text
                    revision_history = extract_revision_history(file_text)
                    if revision_history:
                        revision_histories.append(revision_history)
                    print(f"Revision History for {uploaded_file.name}: {revision_history}")  # 抽出したRevision Historyを表示

            with col2:
                st.subheader("SOP Details")
                revision_history_input += f"{revision_history}, " if revision_history else ""
                revision_history_input = st.text_input("Revision History", value=revision_history_input.strip(", "))

                sections_content = {}

                if 'sections_content' not in st.session_state:
                    st.session_state.sections_content = {}

                if st.button("Generate SOP", key="generate_sop_button"):
                    with st.spinner('SOP作成中...'): 
                        sop_output = generate_sop(main_title, subtitle, combined_text, revision_history_input)
                        if sop_output:  # SOPの生成が成功した場合
                            st.text_area("Created SOP", value=sop_output, height=300)
                            st.session_state.sections_content = sections_content
                            st.session_state.sop_generated = True
                        else:  # SOPの生成に失敗した場合
                            st.error("Failed to generate SOP. Please check the inputs.（SOPの生成に失敗しました。入力を確認してください。）")

                    # SOPと関連ファイルをデータベースに保存
                if st.session_state.sop_generated:
                    if st.button("Save SOP to Database", key="save_sop_button"):
                        with st.spinner('データベースへ保存中...'): 
                            # 必須フィールドが入力されているかチェック
                            if not main_title or not subtitle or not revision_history:
                                st.error('Main Title, Sub Title, および Revision History は必須項目です。')
                            else:
                                session = Session()
                                sections_content = generate_sop(main_title, subtitle, combined_text, revision_history_input)
                                st.session_state.sections_content = sections_content
                                sop_id = save_sop_to_database(main_title, subtitle, revision_history, st.session_state.sections_content)
                                if sop_id is None:
                                    st.warning('A record with the same details already exists.（同じ検査項目、添付資料を持つレコードが既に存在します。）')
                                else:
                                    st.success('SOP and related files have been successfully saved to the database.（SOPとアップロードファイルがデータベースに正常に保存されました。）')

                                if sop_id:
                                    for uploaded_file in uploaded_files:
                                        file_content = BytesIO(uploaded_file.getvalue()).read()
                                        uploaded_file_record = UploadedFile(
                                            sop_id=sop_id,
                                            file_name=uploaded_file.name,
                                            file_content=file_content,
                                            revision_history=revision_history,
                                            registrant_id=1  # Adjust as necessary
                                        )
                                        session.add(uploaded_file_record)
                                    session.commit()
                                    st.success('SOP and related files have been successfully saved to the database.')
                                    # 新しいSOPの作成へ遷移するボタンを表示
                                    if st.button('Create New SOP'):
                                        st.experimental_rerun()
                                else:
                                    st.error('Failed to save SOP details to the database.')

def show_edit_sop_section():
    st.title('SOP Creation with GPT-3.5 Turbo🌏')
    if 'selected_sop_id_for_editing' not in st.session_state:
        st.session_state.selected_sop_id_for_editing = None

    # SOPを選択するためのUIコンポーネントを表示
    sop_list = fetch_sop_list()  # これはSOPリストを取得する関数の例です。実際には自分のデータ構造に合わせて実装してください。
    if sop_list:
        sop_options = [(sop.id, sop.main_title) for sop in sop_list]
        # ここで、ユーザーが選択したSOPのIDをセッション変数に保持します。
        selected_sop_id = st.selectbox(
            'Select SOP to Edit',
            options=[option[0] for option in sop_options],
            format_func=lambda x: next(title for id, title in sop_options if id == x),
            key='sop_selection'
        )

        if st.button('Load SOP for Editing', key='load_sop_for_editing_button'):
            # SOPをロードするためのボタンが押されたら、セッション状態のselected_sop_id_for_editingを更新
            st.session_state.selected_sop_id_for_editing = selected_sop_id
            st.session_state['load_sop'] = True
    else:
        st.error('No SOPs available to edit.')


if __name__ == "__main__":
    main()