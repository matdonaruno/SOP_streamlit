import streamlit as st
import openai
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import tempfile
from utils import extract_text, display_pdf_as_images, extract_revision_history
from database_operations_sql import save_sop_to_database, Session, UploadedFile, SOPDetail, edit_sop_details, fetch_sop_list, save_new_facility_name_if_not_exists, fetch_facility_names_from_database, fetch_facility_id_by_name, add_departmental_sop, add_equipment_sop, fetch_departmental_sops_by_facility, get_departmental_sop_details, update_departmental_sop, check_departmental_sop_exists, get_equipment_sop_details, update_equipment_sop, fetch_equipment_sops_by_facility, check_sop_exists, initialize_database
from additional_sop import addSOPfile
from gpts import ask_gpt, fetch_sop_by_facility
from streamlit_option_menu import option_menu
from output import output_csv, fetch_facilities
from mysop_discriptions import show_sop_descriptions
from generate_sop import generate_sop, generate_dep_sop
from concurrent.futures import ThreadPoolExecutor
from streamlit_searchbox import st_searchbox

executor = ThreadPoolExecutor(max_workers=4)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(layout="wide")
#st.title('SOP Creation with GPT-3.5 Turbo🌏')

# モデルを格納するためのグローバル変数
whisper_model = None

def show_home_section():

    st.title('Welcome to the SOP Manager')
    st.write('This is the home page of the SOP management application. From here, you can navigate to other sections using the menu on the left.Choose "Create New SOP" to add a new Standard Operating Procedure, or select "Edit SOP" to modify an existing one.')
    st.write('(SOP管理アプリケーションのホームページへようこそ。ここでは、左側のメニューを使用して他のセクションへのナビゲーションが可能です。「Create New SOP」を選択して新しい標準作業手順書を追加するか、「Edit SOP」を選択して既存のものを編集してください。)')

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

    # SOPのIDとタイトルの辞書を作成
    sop_dict = {sop.id: sop.main_title for sop in sop_list}

    # タイトルのリストで検索ボックスを表示
    selected_title = st_searchbox(options=list(sop_dict.values()), label="Select SOP to edit")

    # 選択されたタイトルに基づいてIDを取得
    sop_id = None
    for id, title in sop_dict.items():
        if title == selected_title:
            sop_id = id
            break

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

def load_sop(sop_id):
    session = Session()
    sop_data = session.query(SOPDetail).filter(SOPDetail.id == sop_id).first()
    if sop_data:
        # 各フィールドをセッションステートに保存
        st.session_state[f"main_title_{sop_id}"] = sop_data.main_title
        st.session_state[f"subtitle_{sop_id}"] = sop_data.subtitle
        st.session_state[f"revision_history_{sop_id}"] = sop_data.revision_history
        st.session_state[f"measurement_method_{sop_id}"] = sop_data.measurement_method
        st.session_state[f"measurement_principle_{sop_id}"] = sop_data.measurement_principle
        st.session_state[f"parameters_{sop_id}"] = sop_data.parameters
        st.session_state[f"linearity_{sop_id}"] = sop_data.linearity
        st.session_state[f"accuracy_{sop_id}"] = sop_data.accuracy
        st.session_state[f"reproducibility_{sop_id}"] = sop_data.reproducibility
        st.session_state[f"limit_of_quantitation_{sop_id}"] = sop_data.limit_of_quantitation
        st.session_state[f"instrument_difference_{sop_id}"] = sop_data.instrument_difference
        st.session_state[f"sample_type_{sop_id}"] = sop_data.sample_type
        st.session_state[f"sample_storage_{sop_id}"] = sop_data.sample_storage
        st.session_state[f"patient_preparation_{sop_id}"] = sop_data.patient_preparation
        st.session_state[f"container_and_additives_{sop_id}"] = sop_data.container_and_additives
        st.session_state[f"measuring_instrument_{sop_id}"] = sop_data.measuring_instrument
        st.session_state[f"equipment_and_tools_{sop_id}"] = sop_data.equipment_and_tools
        st.session_state[f"reagents_and_composition_{sop_id}"] = sop_data.reagents_and_composition
        st.session_state[f"reagent_preparation_{sop_id}"] = sop_data.reagent_preparation
        st.session_state[f"reagent_storage_and_expiry_{sop_id}"] = sop_data.reagent_storage_and_expiry
        st.session_state[f"sampling_amount_{sop_id}"] = sop_data.sampling_amount
        st.session_state[f"required_volume_{sop_id}"] = sop_data.required_volume
        st.session_state[f"environment_{sop_id}"] = sop_data.environment
        st.session_state[f"safety_management_{sop_id}"] = sop_data.safety_management
        st.session_state[f"standard_solution_preparation_and_storage_{sop_id}"] = sop_data.standard_solution_preparation_and_storage
        st.session_state[f"calibration_curve_{sop_id}"] = sop_data.calibration_curve
        st.session_state[f"result_judgement_{sop_id}"] = sop_data.result_judgement
        st.session_state[f"calibration_implementation_{sop_id}"] = sop_data.calibration_implementation
        st.session_state[f"traceability_{sop_id}"] = sop_data.traceability
        st.session_state[f"operation_steps_{sop_id}"] = sop_data.operation_steps
        st.session_state[f"accuracy_control_sample_preparation_and_storage_{sop_id}"] = sop_data.accuracy_control_sample_preparation_and_storage
        st.session_state[f"internal_accuracy_management_{sop_id}"] = sop_data.internal_accuracy_management
        st.session_state[f"accuracy_control_tolerance_{sop_id}"] = sop_data.accuracy_control_tolerance
        st.session_state[f"external_accuracy_management_{sop_id}"] = sop_data.external_accuracy_management
        st.session_state[f"interference_and_cross_reactivity_{sop_id}"] = sop_data.interference_and_cross_reactivity
        st.session_state[f"analysis_result_calculation_method_{sop_id}"] = sop_data.analysis_result_calculation_method
        st.session_state[f"measurement_uncertainty_{sop_id}"] = sop_data.measurement_uncertainty
        st.session_state[f"instructions_for_determining_quantitative_results_outside_the_measurement_range_{sop_id}"] = sop_data.instructions_for_determining_quantitative_results_outside_the_measurement_range
        st.session_state[f"reinspection_criteria_{sop_id}"] = sop_data.reinspection_criteria
        st.session_state[f"data_selection_criteria_for_reinspection_{sop_id}"] = sop_data.data_selection_criteria_for_reinspection
        st.session_state[f"alert_values_and_critical_values_{sop_id}"] = sop_data.alert_values_and_critical_values
        st.session_state[f"clinical_significance_{sop_id}"] = sop_data.clinical_significance
        st.session_state[f"related_items_{sop_id}"] = sop_data.related_items
        st.session_state[f"possible_variability_factors_{sop_id}"] = sop_data.possible_variability_factors
        st.session_state[f"references_{sop_id}"] = sop_data.references

    session.close()

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
        new_facility_name = st.text_input("Enter New Facility Name")
        if new_facility_name:
            facility_id = save_new_facility_name_if_not_exists(new_facility_name)
    else:
        facility_id = fetch_facility_id_by_name(selected_facility_name)

    # Department titleの設定
    department_title = st.text_input("Department Title")
    # 重複チェック
    if department_title and facility_id:
        existing_sop_check = check_departmental_sop_exists(facility_id, department_title)
        if existing_sop_check:
            st.error("同じ部門で同じタイトルのSOPが既に存在します。別のタイトルを選んでください。")
            return

    # 選択されたファイルタイプのラジオボタン
    file_type = st.radio("Select the type of file you want to upload:", ('PDF/Text Files', 'Audio Files'))

    # 部門SOPの詳細の入力
    section_title = st.text_input("Section Title")
    abstract = st.text_area("Abstract")
    department_details = st.text_area("Department Details")

    # アップロードファイルの処理
    combined_text = ""
    if file_type == 'PDF/Text Files':
        uploaded_files = st.file_uploader("Upload SOP-related files", accept_multiple_files=True, type=['pdf', 'txt'])
        if uploaded_files:
            combined_text = process_uploaded_files(uploaded_files, department_title)

    elif file_type == 'Audio Files':
        uploaded_audio_files = st.file_uploader("Upload Audio Files", accept_multiple_files=True, type=['mp3', 'wav', 'm4a'])
        if uploaded_audio_files:
            combined_text = process_uploaded_audio_files(uploaded_audio_files, department_title)

    # GPTを使用してテキスト生成
    if combined_text and st.button("Generate Text with GPT"):
        generated_text = generate_dep_sop(department_title, combined_text)
        department_details += "\n\n" + generated_text

    # SOPをデータベースに保存
    if st.button("Save Departmental SOP") and facility_id and department_title and section_title and not existing_sop_check:
        details = {
            "section_title": section_title,
            "abstract": abstract,
            "details": department_details
        }
        sop_id, message = add_equipment_sop(facility_id, department_title, details)
        if sop_id:
            st.success(f"Equipment SOP saved successfully. ID: {sop_id}")
            st.session_state.sections = []  # セッションステートのリセット
        else:
            st.error(f"Failed to save Equipment SOP. Error: {message}")
    elif not department_title:
        st.error("Please enter an equipment title.")

def show_edit_departmental_sop_section():
    st.title("Edit Departmental SOP")

    # 施設名の選択
    facility_names = fetch_facility_names_from_database()
    selected_facility_name = st.selectbox("Select Facility", options=facility_names)
    facility_id = fetch_facility_id_by_name(selected_facility_name) if selected_facility_name else None

    if facility_id:
        # 施設IDに基づいて部署SOPのリストを取得
        department_sops = fetch_departmental_sops_by_facility(facility_id)
        if department_sops:
            department_sop_titles = [sop.department_title for sop in department_sops]
            selected_department_sop_title = st.selectbox("Select Department SOP", options=department_sop_titles)

            # 選択した部署SOPのIDを取得
            selected_sop_id = next((sop.id for sop in department_sops if sop.department_title == selected_department_sop_title), None)

            # 選択した部署SOPの詳細の表示と編集
            if selected_sop_id:
                selected_sop_details = get_departmental_sop_details(selected_sop_id)
                if selected_sop_details:
                    with st.form("edit_sop_form"):
                        for key, value in selected_sop_details.items():
                            st.text_area(key.capitalize(), value=value)

                        additional_data_title = st.text_input("Additional Data Title")
                        additional_data_content = st.text_area("Additional Data Content")

                        editor_name = st.text_input("Editor Name")

                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            updated_details = {key: st.session_state[key] for key in selected_sop_details.keys()}
                            if additional_data_title:
                                updated_details[additional_data_title] = additional_data_content
                            save_status, message = update_departmental_sop(selected_sop_id, updated_details, editor_name)
                            if save_status:
                                st.success(f"Changes saved successfully. {message}")
                            else:
                                st.error(f"Failed to save changes. {message}")
                else:
                    st.error("No SOP details found for the selected department.")
        else:
            st.error("No departmental SOPs available for the selected facility.")
    else:
        st.error("Please select a facility.")

def get_departmental_sop_details(facility_id, department_title):
    # ここでデータベースから選択された部署SOPの詳細を取得
    # ダミーのデータ構造を返します
    return {'section_title': "Sample Section", 'content': "This is a sample SOP content."}

def update_departmental_sop(sop_id, updated_details, editor_name):
    # ここでデータベースを更新
    # 更新が成功したかどうかのステータスとメッセージを返します
    return True, "Update successful"

def show_add_equipment_sop_section():
    st.title("Add New Equipment SOP")

    # 施設名の選択
    facility_names = fetch_facility_names_from_database()
    selected_facility_name = st.selectbox("Select Facility", options=facility_names + ["Add new..."])
    facility_id = None
    if selected_facility_name == "Add new...":
        new_facility_name = st.text_input("Enter New Facility Name")
        if new_facility_name:
            facility_id = save_new_facility_name_if_not_exists(new_facility_name)
    else:
        facility_id = fetch_facility_id_by_name(selected_facility_name)

    # Equipment titleの設定
    equipment_title = st.text_input("Equipment Title")
    # 重複チェック
    if equipment_title and facility_id:
        existing_sop_check = check_departmental_sop_exists(facility_id, equipment_title)
        if existing_sop_check:
            st.error("同じ部門で同じタイトルのSOPが既に存在します。別のタイトルを選んでください。")
            return

    # 選択されたファイルタイプのラジオボタン
    file_type = st.radio("Select the type of file you want to upload:", ('PDF/Text Files', 'Audio Files'))

    # 機器タイトルと詳細の入力
    section_title = st.text_input("Section Title")
    abstract = st.text_area("Abstract")
    equipment_details = st.text_area("Equipment Details")

    # アップロードファイルの処理
    combined_text = ""
    if file_type == 'PDF/Text Files':
        uploaded_files = st.file_uploader("Upload SOP-related files", accept_multiple_files=True, type=['pdf', 'txt'])
        if uploaded_files:
            combined_text = process_uploaded_files(uploaded_files, equipment_title)

    elif file_type == 'Audio Files':
        uploaded_audio_files = st.file_uploader("Upload Audio Files", accept_multiple_files=True, type=['mp3', 'wav', 'm4a'])
        if uploaded_audio_files:
            combined_text = process_uploaded_audio_files(uploaded_audio_files, equipment_title)

    # GPTを使用してテキスト生成
    if combined_text and st.button("Generate Text with GPT"):
        generated_text = generate_dep_sop(equipment_title, combined_text)
        equipment_details += "\n\n" + generated_text

    # SOPをデータベースに保存
    if st.button("Save Equipment SOP") and facility_id and equipment_title and section_title and not existing_sop_check:
        details = {
            "section_title": section_title,
            "abstract": abstract,
            "details": equipment_details
        }
        sop_id, message = add_equipment_sop(facility_id, equipment_title, details)
        if sop_id:
            st.success(f"Equipment SOP saved successfully. ID: {sop_id}")
            st.session_state.sections = []  # セッションステートのリセット
        else:
            st.error(f"Failed to save Equipment SOP. Error: {message}")
    elif not equipment_title:
        st.error("Please enter an equipment title.")

def show_edit_equipment_sop_section():
    st.title("Edit Equipment SOP")

    # 施設名の選択
    facility_names = fetch_facility_names_from_database()
    selected_facility_name = st.selectbox("Select Facility", options=facility_names)
    facility_id = fetch_facility_id_by_name(selected_facility_name) if selected_facility_name else None

    if facility_id:
        # 施設IDに基づいて部署SOPのリストを取得
        equipment_sops = fetch_equipment_sops_by_facility(facility_id)
        if equipment_sops:
            equipment_sop_titles = [sop.equipment_title for sop in equipment_sops]
            selected_equipment_sop_title = st.selectbox("Select Equipment SOP", options=equipment_sop_titles)

            # 選択した部署SOPのIDを取得
            selected_sop_id = next((sop.id for sop in equipment_sops if sop.equipment_title == selected_equipment_sop_title), None)

            # 選択した部署SOPの詳細の表示と編集
            if selected_sop_id:
                selected_sop_details = get_equipment_sop_details(selected_sop_id)
                if selected_sop_details:
                    with st.form("edit_sop_form"):
                        for key, value in selected_sop_details.items():
                            st.text_area(key.capitalize(), value=value)

                        additional_data_title = st.text_input("Additional Data Title")
                        additional_data_content = st.text_area("Additional Data Content")

                        editor_name = st.text_input("Editor Name")

                        submitted = st.form_submit_button("Save Changes")
                        if submitted:
                            updated_details = {key: st.session_state[key] for key in selected_sop_details.keys()}
                            if additional_data_title:
                                updated_details[additional_data_title] = additional_data_content
                            save_status, message = update_equipment_sop(selected_sop_id, updated_details, editor_name)
                            if save_status:
                                st.success(f"Changes saved successfully. {message}")
                            else:
                                st.error(f"Failed to save changes. {message}")
                else:
                    st.error("No SOP details found for the selected department.")
        else:
            st.error("No Equipment SOPs available for the selected facility.")
    else:
        st.error("Please select a facility.")




def main():
    print("main 関数の開始")
    initialize_database()

    image = Image.open('imagesaidebar.png')
    image = image.resize((300, 250))
    st.sidebar.image(image)

    menu_category = option_menu(
    menu_title="Main Categories",
    options=["Home", "AIに聞いてみる！", "検査項目別SOP Menu", "部署別SOP Menu", "検査機器別SOP Menu"],
    icons=["house", "question-circle", "journal-text", "people-fill", "tools"],
    menu_icon="cast",  # このアイコンはメニュー全体のアイコンを指定
    default_index=0,
    orientation="horizontal"
)

    # Home画面表示
    if menu_category == "Home":
        show_home_section()

    elif menu_category == "AIに聞いてみる！":
        show_ask_gpt_section()

    elif menu_category == "検査項目別SOP Menu":
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
                        measurement_method=st.session_state[f"measurement_method_{sop_id}"],
                        measurement_principle=st.session_state[f"measurement_principle_{sop_id}"],
                        parameters=st.session_state[f"parameters_{sop_id}"],
                        linearity=st.session_state[f"linearity_{sop_id}"],
                        accuracy=st.session_state[f"accuracy_{sop_id}"],
                        reproducibility=st.session_state[f"reproducibility_{sop_id}"],
                        limit_of_quantitation=st.session_state[f"limit_of_quantitation_{sop_id}"],
                        instrument_difference=st.session_state[f"instrument_difference_{sop_id}"],
                        sample_type=st.session_state[f"sample_type_{sop_id}"],
                        sample_storage=st.session_state[f"sample_storage_{sop_id}"],
                        patient_preparation=st.session_state[f"patient_preparation_{sop_id}"],
                        container_and_additives=st.session_state[f"container_and_additives_{sop_id}"],
                        measuring_instrument=st.session_state[f"measuring_instrument_{sop_id}"],
                        equipment_and_tools=st.session_state[f"equipment_and_tools_{sop_id}"],
                        reagents_and_composition=st.session_state[f"reagents_and_composition_{sop_id}"],
                        reagent_preparation=st.session_state[f"reagent_preparation_{sop_id}"],
                        reagent_storage_and_expiry=st.session_state[f"reagent_storage_and_expiry_{sop_id}"],
                        sampling_amount=st.session_state[f"sampling_amount_{sop_id}"],
                        required_volume=st.session_state[f"required_volume_{sop_id}"],
                        environment=st.session_state[f"environment_{sop_id}"],
                        safety_management=st.session_state[f"safety_management_{sop_id}"],
                        standard_solution_preparation_and_storage=st.session_state[f"standard_solution_preparation_and_storage_{sop_id}"],
                        calibration_curve=st.session_state[f"calibration_curve_{sop_id}"],
                        result_judgement=st.session_state[f"result_judgement_{sop_id}"],
                        calibration_implementation=st.session_state[f"calibration_implementation_{sop_id}"],
                        traceability=st.session_state[f"traceability_{sop_id}"],
                        operation_steps=st.session_state[f"operation_steps_{sop_id}"],
                        accuracy_control_sample_preparation_and_storage=st.session_state[f"accuracy_control_sample_preparation_and_storage_{sop_id}"],
                        internal_accuracy_management=st.session_state[f"internal_accuracy_management_{sop_id}"],
                        accuracy_control_tolerance=st.session_state[f"accuracy_control_tolerance_{sop_id}"],
                        external_accuracy_management=st.session_state[f"external_accuracy_management_{sop_id}"],
                        interference_and_cross_reactivity=st.session_state[f"interference_and_cross_reactivity_{sop_id}"],
                        analysis_result_calculation_method=st.session_state[f"analysis_result_calculation_method_{sop_id}"],
                        measurement_uncertainty=st.session_state[f"measurement_uncertainty_{sop_id}"],

                        instructions_for_determining_quantitative_results_outside_the_measurement_range=st.session_state[f"instructions_for_determining_quantitative_results_outside_the_measurement_range_{sop_id}"],
                        reinspection_criteria=st.session_state[f"reinspection_criteria_{sop_id}"],
                        data_selection_criteria_for_reinspection=st.session_state[f"data_selection_criteria_for_reinspection_{sop_id}"],
                        alert_values_and_critical_values=st.session_state[f"alert_values_and_critical_values_{sop_id}"],
                        clinical_significance=st.session_state[f"clinical_significance_{sop_id}"],
                        related_items=st.session_state[f"related_items_{sop_id}"],
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

    elif menu_category == "部署別SOP Menu":
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
            show_edit_departmental_sop_section()

        elif selected == "View Departmental SOPs":
            show_add_departmental_sop_section()

    elif menu_category == "検査機器別SOP Menu":
        with st.sidebar:
            selected = option_menu(menu_title="",
                                options=["Add New Equipment SOP", "Edit Equipment SOP", "View Equipment SOPs"],
                                icons=["eye", "file-earmark-plus", "pencil"], 
                                menu_icon="tools",  # カスタムアイコン
                                default_index=0  # デフォルトの選択項目
                                )
        # 選択に応じて表示

        if selected == "Add New Equipment SOP":
            show_add_equipment_sop_section()
        elif selected == "Edit Equipment SOP":
            show_add_equipment_sop_section()
        elif selected == "View Equipment SOPs":
            show_add_equipment_sop_section()


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
                                    st.success('SOP and related files have been successfully saved to the database.（SOPとアップロードファイルがデータベースに正常に保存されました。）')
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
            load_sop(selected_sop_id)  # SOPのデータをロードしてセッションステートにセット
            st.session_state.selected_sop_id_for_editing = selected_sop_id
    else:
        st.error('No SOPs available to edit.')


if __name__ == "__main__":
    main()