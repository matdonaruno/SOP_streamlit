import streamlit as st
import tempfile
import os
from io import BytesIO
from database_operations_sql import (
    Session,
    Facility,
    SOPDetail,
    EditedSOP,
    save_sop_to_database,
    UploadedFile,
    UncertaintyFactorDiagram
)
from utils import extract_text, display_pdf_as_images, extract_revision_history
from generate_sop import generate_sop_for_selected_sections



def select_facility_and_sop():
    session = Session()
    try:
        facilities = session.query(Facility).all()
        if not facilities:
            st.error("No facilities available. Please add facilities first.")
            return None, None, None

        facility_names = [facility.name for facility in facilities]
        selected_facility = st.selectbox("Select Facility", facility_names)

        if selected_facility:
            facility_id = [facility.id for facility in facilities if facility.name == selected_facility][0]
            sops = session.query(EditedSOP).filter(EditedSOP.facility_id == facility_id).all()
            
            if not sops:
                st.error("No SOPs available for the selected facility.")
                return selected_facility, None, None

            main_titles = list(set([sop.main_title for sop in sops]))
            selected_main_title = st.selectbox("Select Main Title", main_titles)

            if selected_main_title:
                subtitles = [sop.subtitle for sop in sops if sop.main_title == selected_main_title]
                selected_subtitle = st.selectbox("Select Sub Title", subtitles)
                return selected_facility, selected_main_title, selected_subtitle
            else:
                return selected_facility, None, None
        else:
            return None, None, None

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None, None

    finally:
        session.close()



def upload_and_process_file(subtitle):
    uploaded_file = st.file_uploader("Upload additional SOP file", type=['pdf', 'txt'])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            display_pdf_as_images(tmp_file.name, subtitle)
            os.unlink(tmp_file.name)
        
        file_text = extract_text(BytesIO(uploaded_file.getvalue()), uploaded_file.type)
        revision_history = extract_revision_history(file_text)
        return (file_text, revision_history), uploaded_file
    return None, None

def select_main_title_and_sop_sections(selected_facility, selected_main_title, selected_subtitle):
    session = Session()
    try:
        # 施設IDを取得
        facility_id = session.query(Facility).filter(Facility.name == selected_facility).first().id
        
        # 選択された施設、メインタイトル、サブタイトルに基づいてSOPを取得
        sop = session.query(EditedSOP).filter(
            EditedSOP.facility_id == facility_id,
            EditedSOP.main_title == selected_main_title,
            EditedSOP.subtitle == selected_subtitle
        ).first()
        
        if sop:
            # SOPが存在する場合、更新するセクションを選択
            sop_sections = [
                "測定法", "測定原理", "パラメーター", "直進性", "正確性", "同時再現性", "定量下限",
                "機器間差", "サンプルの種類", "サンプルの保管方法", "患者準備", "容器および添加剤の種類",
                "測定機器", "必要な機材および器具", "試薬および構成", "試薬の調整",
                "試薬保管条件および有効期限", "サンプリング量", "必要量", "環境", "安全管理",
                "標準液の調整および保管条件", "検量線", "結果の判定", "校正の実施", "トレーサビリティ",
                "操作ステップ", "精度管理試料の調整および保管条件", "内部精度管理", "精度管理許容限界",
                "外部精度管理", "干渉および交差反応", "分析結果の計算法", "測定の不確かさ",
                "不確かさの要因図", "結果が測定範囲外であった場合の定量結果決定に関する指示",
                "再検基準", "再検時のデータ選択基準", "警戒値・緊急異常値", "臨床的意義",
                "関連項目", "可能性のある変動要因", "References", "作成者", "文書管理者", "初版",
                "版数（改版履歴）"
            ]
            selected_sections = st.multiselect("Select sections to update", options=sop_sections)
            return sop, selected_sections
        else:
            st.error("No SOP found for the selected criteria.")
            return None, None
    finally:
        session.close()


def addSOPfile():
    st.title("Additional SOPs")
    selected_facility, selected_main_title, selected_subtitle = select_facility_and_sop()
    
    if not selected_facility or not selected_main_title or not selected_subtitle:
        st.error("Please select all required fields: Facility, Main Title, and Sub Title.")
        return

    sop, selected_sections = select_main_title_and_sop_sections(selected_facility, selected_main_title, selected_subtitle)
    
    if not sop:
        st.error("No SOP found for the selected criteria.")
        return

    session = Session()
    try:
        sop_details = session.query(SOPDetail).filter(SOPDetail.edited_sop_id == sop.id).all()
        sections_content = {detail.section: detail.content for detail in sop_details if detail.section in selected_sections}

        for section in selected_sections:
            st.subheader(f"Edit Section: {section}")
            editable_content = st.text_area("Content", value=sections_content.get(section, ""), key=f"editable_{section}")
            sections_content[section] = editable_content

        if st.button('Save Changes'):
            for section, content in sections_content.items():
                detail = session.query(SOPDetail).filter(SOPDetail.edited_sop_id == sop.id, SOPDetail.section == section).first()
                if detail:
                    detail.content = content
                else:
                    new_detail = SOPDetail(edited_sop_id=sop.id, section=section, content=content)
                    session.add(new_detail)
            session.commit()
            st.success("SOP updates have been successfully saved.")
    finally:
        session.close()


