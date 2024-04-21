import streamlit as st
import openai
import json
from io import BytesIO
import os
from dotenv import load_dotenv
import tempfile
from utils import extract_text, display_pdf_as_images, extract_revision_history
from database_operations_sql import save_sop_to_database, Session, UploadedFile, SOPDetail, edit_sop_details, fetch_sop_list, save_new_facility_name_if_not_exists, fetch_facility_names_from_database, fetch_facility_id_by_name, add_departmental_sop
from additional_sop import addSOPfile
from gpts import ask_gpt, fetch_sop_by_facility
from streamlit_option_menu import option_menu
from output import output_csv, fetch_facilities
from mysop_discriptions import show_sop_descriptions
from generate_sop import generate_sop, generate_dep_sop
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")
#st.title('SOP Creation with GPT-3.5 Turbo🌏')

# モデルを格納するためのグローバル変数
whisper_model = None

def load_whisper_model():
    global whisper_model
    if whisper_model is None:
        from whisper import load_model
        whisper_model = load_model("large")
    return whisper_model

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

    st.text_area("測定法", value=sop_detail.measurement_method, key=f"measurement_method_{sop_id}")
    st.text_area("測定原理", value=sop_detail.measurement_principle, key=f"measurement_principle_{sop_id}")
    st.text_area("パラメーター", value=sop_detail.parameters, key=f"parameters_{sop_id}")
    st.text_area("直進性", value=sop_detail.linearity, key=f"linearity_{sop_id}")
    st.text_area("正確性", value=sop_detail.accuracy, key=f"accuracy_{sop_id}")
    st.text_area("同時再現性", value=sop_detail.reproducibility, key=f"reproducibility_{sop_id}")
    st.text_area("定量下限", value=sop_detail.limit_of_quantitation, key=f"limit_of_quantitation_{sop_id}")
    st.text_area("機器間差", value=sop_detail.instrument_difference, key=f"instrument_difference_{sop_id}")
    st.text_area("サンプルの種類", value=sop_detail.sample_type, key=f"sample_type_{sop_id}")
    st.text_area("サンプルの保管方法", value=sop_detail.sample_storage, key=f"sample_storage_{sop_id}")
    st.text_area("患者準備", value=sop_detail.patient_preparation, key=f"patient_preparation_{sop_id}")
    st.text_area("容器および添加剤の種類", value=sop_detail.container_and_additives, key=f"container_and_additives_{sop_id}")
    st.text_area("測定機器", value=sop_detail.measuring_instrument, key=f"measuring_instrument_{sop_id}")
    st.text_area("必要な機材および器具", value=sop_detail.equipment_and_tools, key=f"equipment_and_tools_{sop_id}")
    st.text_area("試薬および構成", value=sop_detail.reagents_and_composition, key=f"reagents_and_composition_{sop_id}")
    st.text_area("試薬の調整", value=sop_detail.reagent_preparation, key=f"reagent_preparation_{sop_id}")
    st.text_area("試薬保管条件および有効期限", value=sop_detail.reagent_storage_and_expiry, key=f"reagent_storage_and_expiry_{sop_id}")
    st.text_area("サンプリング量", value=sop_detail.sampling_amount, key=f"sampling_amount_{sop_id}")
    st.text_area("必要量", value=sop_detail.required_volume, key=f"required_volume_{sop_id}")
    st.text_area("環境", value=sop_detail.environment, key=f"environment_{sop_id}")
    st.text_area("安全管理", value=sop_detail.safety_management, key=f"safety_management_{sop_id}")
    st.text_area("標準液の調整および保管条件", value=sop_detail.standard_solution_preparation_and_storage, key=f"standard_solution_preparation_and_storage_{sop_id}")
    st.text_area("検量線", value=sop_detail.calibration_curve, key=f"calibration_curve_{sop_id}")
    st.text_area("結果の判定", value=sop_detail.result_judgement, key=f"result_judgement_{sop_id}")
    st.text_area("校正の実施", value=sop_detail.calibration_implementation, key=f"calibration_implementation_{sop_id}")
    st.text_area("トレーサビリティ", value=sop_detail.traceability, key=f"traceability_{sop_id}")
    st.text_area("操作ステップ", value=sop_detail.operation_steps, key=f"operation_steps_{sop_id}")
    st.text_area("精度管理試料の調整および保管条件", value=sop_detail.accuracy_control_sample_preparation_and_storage, key=f"accuracy_control_sample_preparation_and_storage_{sop_id}")
    st.text_area("内部精度管理", value=sop_detail.internal_accuracy_management, key=f"internal_accuracy_management_{sop_id}")
    st.text_area("精度管理許容限界", value=sop_detail.accuracy_control_tolerance, key=f"accuracy_control_tolerance_{sop_id}")
    st.text_area("外部精度管理", value=sop_detail.external_accuracy_management, key=f"external_accuracy_management_{sop_id}")
    st.text_area("干渉および交差反応", value=sop_detail.interference_and_cross_reactivity, key=f"interference_and_cross_reactivity_{sop_id}")
    st.text_area("分析結果の計算法", value=sop_detail.analysis_result_calculation_method, key=f"analysis_result_calculation_method_{sop_id}")
    st.text_area("測定の不確かさ", value=sop_detail.measurement_uncertainty, key=f"measurement_uncertainty_{sop_id}")
    st.text_area("不確かさの要因図", value=sop_detail.uncertainty_factor_diagram, key=f"uncertainty_factor_diagram_{sop_id}")
    st.text_area("結果が測定範囲外であった場合の定量結果決定に関する指示", value=sop_detail.instructions_for_determining_quantitative_results_outside_the_measurement_range, key=f"instructions_for_determining_quantitative_results_outside_the_measurement_range_{sop_id}")
    st.text_area("再検基準", value=sop_detail.reinspection_criteria, key=f"reinspection_criteria_{sop_id}")
    st.text_area("再検時のデータ選択基準", value=sop_detail.data_selection_criteria_for_reinspection, key=f"data_selection_criteria_for_reinspection_{sop_id}")
    st.text_area("警戒値・緊急異常値", value=sop_detail.alert_values_and_critical_values, key=f"alert_values_and_critical_values_{sop_id}")
    st.text_area("臨床的意義", value=sop_detail.clinical_significance, key=f"clinical_significance_{sop_id}")
    st.text_area("関連項目", value=sop_detail.related_items, key=f"related_items_{sop_id}")
    st.text_area("可能性のある変動要因", value=sop_detail.possible_variability_factors, key=f"possible_variability_factors_{sop_id}")
    st.text_area("References", value=sop_detail.references, key=f"references_{sop_id}")

    st.text_input("作成者", key=f"creator_editor_{sop_id}")
    st.text_input("認証者", key=f"approver_{sop_id}")
    st.text_input("文書管理者", key=f"document_manager_{sop_id}")
    st.text_area("初版", key=f"first_revision_{sop_id}")
    st.text_area("版数（改版履歴）", key=f"own_revision_history_{sop_id}")

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

def transcribe_audio(uploaded_file):
    model = load_whisper_model()

    with st.spinner('音声を文字起こし中...'):
        progress_bar = st.progress(0)  # プログレスバーの初期化
        # アップロードされたファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name  # 一時ファイルのパスを取得
            progress_bar.progress(50)  # 50% 進捗を表示
            # 一時ファイルのパスを使用して文字起こし
            result = model.transcribe(tmp_path)
            progress_bar.progress(100)  # 完了を表示
    return result["text"]

def process_uploaded_files(uploaded_files, section_title):
    combined_text = ""
    # Streamlitのカラムを作成
    col1, col2 = st.columns([1, 2])  # 例えば、左側のカラムを1の幅に、右側を2の幅に設定
    
    with col1:
        st.subheader("Uploaded Files Previews")
        for uploaded_file in uploaded_files:
            # プレビュー表示
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                # PDFファイルのプレビュー画像を表示
                display_pdf_as_images(tmp_file.name, section_title)  # Display PDF as images with section_title
                os.unlink(tmp_file.name)
    
    with col2:
        st.subheader("Extracted Text")
        for uploaded_file in uploaded_files:
            # PDFからテキストを抽出する関数（これは既に定義されているものとします）
            file_text = extract_text(uploaded_file)
            combined_text += "\n" + file_text
            # 抽出されたテキストの一部を表示（全てを表示すると長くなりすぎる場合があるため）
            st.text_area("Extracted Text Preview", value=file_text[:500] + "...", height=100)

    return combined_text

def process_uploaded_audio_files(uploaded_audio_files, section_title):
    transcribed_texts = []
    # Streamlitのカラムを作成
    col1, col2 = st.columns([1, 2])  # 例えば、左側のカラムを1の幅に、右側を2の幅に設定

    with col1:
        st.subheader("Uploaded Audio Files")
        for uploaded_audio_file in uploaded_audio_files:
            # アップロードされた音声ファイルの情報を表示
            st.audio(uploaded_audio_file, format="audio/wav", start_time=0)

    with col2:
        st.subheader("Transcribed Text")
        for uploaded_audio_file in uploaded_audio_files:
            # 音声ファイルからテキストを文字起こしする関数
            transcribed_text = transcribe_audio(uploaded_audio_file)
            transcribed_texts.append(transcribed_text)
            # 文字起こししたテキストのプレビューを表示（全てを表示すると長くなりすぎる場合があるため）
            st.text_area("Transcribed Text Preview", value=transcribed_text[:500] + "...", height=100)

        combined_transcribed_text = " ".join(transcribed_texts)
    
    return combined_transcribed_text


def show_add_departmental_sop_section():
    st.title("Add New Departmental SOP")

    # 施設名の選択
    facility_names = fetch_facility_names_from_database()
    selected_facility_name = st.selectbox("Select Facility", options=facility_names + ["Add new..."])
    facility_id = None
    if selected_facility_name == "Add new...":
        new_facility_name = st.text_input("New Facility Name")
        if new_facility_name:
            facility_id = save_new_facility_name_if_not_exists(new_facility_name)
    else:
        facility_id = fetch_facility_id_by_name(selected_facility_name)

    # 選択されたファイルタイプのラジオボタン
    file_type = st.radio("Select the type of file you want to upload:", ('PDF/Text Files', 'Audio Files'))

    # セクションの入力
    if 'sections' not in st.session_state:
        st.session_state.sections = []

    section_title = st.text_input("Section Title")
    abstract = st.text_area("Abstract")
    department_details = st.text_area("Department Details")

    # ファイルタイプに基づいて異なるアップロードフォームを表示
    if file_type == 'PDF/Text Files':
        uploaded_files = st.file_uploader("Upload SOP-related files", accept_multiple_files=True, type=['pdf', 'txt'])
        if uploaded_files:
            combined_text = process_uploaded_files(uploaded_files, section_title)
            # ここで、combined_textを使って何か処理をする
            if st.button("Generate Text with GPT"):
                generated_text = generate_dep_sop(section_title, combined_text)
                department_details = generated_text
                st.text_area("Generated Department Details", value=department_details, height=300)

    elif file_type == 'Audio Files':
        uploaded_audio_files = st.file_uploader("Upload Audio Files", accept_multiple_files=True, type=['mp3', 'wav', 'm4a'])
        if uploaded_audio_files:
            transcribed_text = process_uploaded_audio_files(uploaded_audio_files)
            # ここで、transcribed_textを使って何か処理をする
            if st.button("Transcribe and Generate Text"):
                generated_sop_section = generate_dep_sop(transcribed_text)
                st.text_area("Generated SOP Section", value=generated_sop_section, height=300)


    # セクションを追加
    if st.button("Save Section and Add New Section"):
        st.session_state.sections.append({
            "section_title": section_title,
            "abstract": abstract,
            "details": department_details
        })
        # 新しいセクションの入力を促す
        st.experimental_rerun()

    # すべてのセクションを保存
    if st.button("Save Departmental SOP"):
        if facility_id and st.session_state.department_title and st.session_state.dep_revision_history and st.session_state.sections:
            details = {"sections": st.session_state.sections, "department_title": st.session_state.department_title, "dep_revision_history": st.session_state.dep_revision_history}
            sop_id = add_departmental_sop(facility_id, st.session_state.department_title, details)
            if sop_id:
                st.success("Departmental SOP saved successfully.")
                st.session_state.sections = []  # セッションステートのリセット
                st.session_state.department_title = ''
                st.session_state.dep_revision_history = ''
            else:
                st.error("Failed to save Departmental SOP.")
        else:
            st.error("Please complete all fields.")





def main():
    print("main 関数の開始")

    st.sidebar.title("Menu")
    # メニューカテゴリ選択
    menu_category = st.sidebar.selectbox("Select Category", ["Home", "AI Answers Your SOP Lists", "Section-specific SOP Menu", "Departmental SOP Menu", "Equipment-Specific SOP Menu"])

    # Home画面表示
    if menu_category == "Home":
        show_home_section()

    elif menu_category == "AI Answers Your SOP Lists":
        show_ask_gpt_section()

    elif menu_category == "Section-specific SOP Menu":
        with st.sidebar:
            selected = option_menu(menu_title="",
                                options=["Create New SOP", "Edit SOP", "Additional SOPs", "My SOP Discriptions", "Output CSV"],
                                icons=["file-earmark-pdf", "pencil", "file-earmark-plus-fill", "file-text", "cloud-download"],
                                menu_icon="list-ol",  # カスタムアイコン
                                default_index=0  # デフォルトの選択項目
                                )
        # 選択に応じて表示
        if selected == "Create New SOP":
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

    elif menu_category == "Departmental SOP Menu":
        with st.sidebar:
            selected = option_menu(menu_title="",
                            options=["Add New Departmental SOP",  "Edit Departmental SOP", "View Departmental SOPs"],
                            icons=["eye", "file-earmark-plus", "pencil"],
                            menu_icon="hand-index-thumb-fill",  # カスタムアイコン
                            default_index=0  # デフォルトの選択項目
                            )

        if selected == "Add New Departmental SOP":
            show_add_departmental_sop_section()

        if selected == "Edit Departmental SOP":
            show_add_departmental_sop_section()

        elif selected == "View Departmental SOPs":
            show_add_departmental_sop_section()

    elif menu_category == "Equipment-Specific SOP Menu":
        with st.sidebar:
            selected = option_menu(menu_title="",
                                options=["Add New Equipment SOP", "Edit Equipment SOP", "View Equipment SOPs"],
                                icons=["eye", "file-earmark-plus", "pencil"], 
                                menu_icon="tools",  # カスタムアイコン
                                default_index=0  # デフォルトの選択項目
                                )
        # 選択に応じて表示
        if selected == "View Equipment SOPs":
            show_create_sop_section()
        elif selected == "Add New Equipment SOP":
            show_edit_sop_section()
        elif selected == "Edit Equipment SOP":
            show_edit_sop_section()


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