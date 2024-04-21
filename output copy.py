import streamlit as st
from database_operations_sql import Session, Facility, EditedSOP
import pandas as pd

def fetch_facilities():
    session = Session()
    facilities = session.query(Facility).all()
    session.close()
    return facilities

def fetch_sops_by_facility_id(facility_id):
    session = Session()
    sops = session.query(EditedSOP).filter(EditedSOP.facility_id == facility_id).all()
    session.close()
    return sops

def download_sop_details(sop_id):
    session = Session()
    sop = session.query(EditedSOP).filter(EditedSOP.id == sop_id).first()
    session.close()
    if sop:
        # SOPの詳細をDataFrameに変換
        data = {
            "組織名": ["NaN"],
            "施設名": ["NaN"],
            "部署": ["NaN"],
            "文書番号": ["NaN"],
            "文書名": ["NaN"],
            "版数": ["NaN"],
            "作成者": [sop.creator_editor],
            "確認者": ["Nan"],
            "承認者": [sop.approver],
            "文書管理者": [sop.document_manager],
            "初版承認日": ["Nan"],
            "初版使用開始日": ["Nan"],
            "Main Title": [sop.main_title],
            "Sub Title": [sop.subtitle],
            "Purpose": [sop.purpose],
            "Procedure Principle": [sop.procedure_principle],
            "Performance Characteristics": [sop.performance_characteristics],
            "Sample Type": [sop.sample_type],
            "Patient Preparation": [sop.patient_preparation],
            "Container": [sop.container],
            "Equipment and Reagents": [sop.equipment_and_reagents],
            "Environmental and Safety Management": [sop.environmental_and_safety_management],
            "Calibration Procedure": [sop.calibration_procedure],
            "Operation Steps": [sop.operation_steps],
            "Accuracy Control Procedures": [sop.accuracy_control_procedures],
            "Interference and Cross Reactivity": [sop.interference_and_cross_reactivity],
            "Result Calculation Principle": [sop.result_calculation_principle],
            "Biological Reference Range": [sop.biological_reference_range],
            "Instructions for Out of Range Results": [sop.instructions_for_out_of_range_results],
            "Reinspection Procedure": [sop.reinspection_procedure],
            "Alert Values": [sop.alert_values],
            "Clinical Interpretation": [sop.clinical_interpretation],
            "Possible Variability Factors": [sop.possible_variability_factors],
            "References": [sop.references],
            "Facility ID": [sop.facility_id],
            "Creator/Editor Timestamp": [sop.creator_editor_timestamp],
            "Approver": [sop.approver],
            "Approver Timestamp": [sop.approver_timestamp],
            "Document Manager": [sop.document_manager],
            "Document Manager Timestamp": [sop.document_manager_timestamp],
            "Own Revision History": [sop.own_revision_history],
            "Created At": [sop.created_at]
        }

        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode('utf-8')
    return None

def output_csv():
    st.title('Output SOP Details to CSV')

    # 施設の選択
    facilities = fetch_facilities()
    facility_names = [facility.name for facility in facilities]
    selected_facility_name = st.selectbox("Select Facility", facility_names)

    # 選択した施設に関連するSOPのリストを表示
    if selected_facility_name:
        selected_facility = next((facility for facility in facilities if facility.name == selected_facility_name), None)
        if selected_facility:
            sops = fetch_sops_by_facility_id(selected_facility.id)
            sop_options = [(sop.id, sop.main_title) for sop in sops]
            selected_sop_id = st.selectbox("Select SOP", [option[0] for option in sop_options], format_func=lambda x: next(title for id, title in sop_options if id == x))

            # CSVとしてダウンロード
            if st.button("Download CSV"):
                csv = download_sop_details(selected_sop_id)
                if csv:
                    st.download_button(label="Download SOP as CSV", data=csv, file_name="sop_details.csv", mime='text/csv')
                else:
                    st.error("Failed to fetch SOP details.")
