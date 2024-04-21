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
            "版数": [sop.own_revision_history],
            "作成者": [sop.creator_editor],
            "確認者": ["Nan"],
            "承認者": [sop.approver],
            "文書管理者": [sop.document_manager],
            "初版承認日": ["Nan"],
            "初版使用開始日": ["Nan"],
            "Main Title": [sop.main_title],
            "Sub Title": [sop.subtitle],
            "検査の目的": [sop.purpose],
            "Procedure Principle": [sop.procedure_principle],
            "測定方法": [sop.procedure_principle],
            "測定原理": ["Nan"],
            "パラメーター": ["Nan"],
            "性能特性": ["Nan"],
            "同時再現性": [sop.performance_characteristics],
            "定量下限": ["Nan"],
            "機器間差": ["Nan"],
            "Sample Type": ["Nan"],
            "サンプルの種類": [sop.sample_type],
            "サンプルの貯法": ["Nan"],
            "Patient Preparation": [sop.patient_preparation],
            "Container": [sop.container],
            "必要な機材および試薬": ["Nan"],
            "測定機器": ["Nan"],
            "Equipment and Reagents": [sop.equipment_and_reagents],
            "試薬の調整": ["Nan"],
            "試薬保管条件および有効期限": ["Nan"],
            "サンプリング量": ["Nan"],
            "必要量": ["Nan"],
            "環境および安全管理": ["Nan"],
            "環境": [sop.environmental_and_safety_management],
            "安全管理": [sop.environmental_and_safety_management],
            "校正手順": ["Nan"],
            "標準液の調整および保管条件": ["Nan"],
            "検量線": ["Nan"],
            "結果判定": ["Nan"],
            "校正の実施": [sop.calibration_procedure],
            "トレーサビリティ": ["Nan"],
            "操作ステップ": [sop.operation_steps],
            "精度管理手順": ["Nan"],
            "精度管理用試料の調整および保存条件": [sop.accuracy_control_procedures],
            "内部精度管理": [sop.interference_and_cross_reactivity],
            "精度管理許容限界を外れた場合の検体の対処法": ["Nan"],
            "外部精度管理": ["Nan"],
            "干渉および交差反応": ["Nan"],
            "結果計算法の原理・測定の不確かさを含む": ["Nan"],
            "分析結果の計算法": [sop.result_calculation_principle],
            "測定の不確かさ": [sop.result_calculation_principle],
            "不確かさの要因図": ["Nan"],
            "Biological Reference Range": [sop.biological_reference_range],
            "結果が測定範囲外であった場合の定量結果決定に関する指示": ["Nan"],
            "再検基準": [sop.reinspection_procedure],
            "再検時のデータ選択基準": [sop.instructions_for_out_of_range_results],
            "Alert Values": [sop.alert_values],
            "検査室の臨床的解釈": ["Nan"],
            "臨床的意義": [sop.clinical_interpretation],
            "関連項目": ["Nan"],
            "Possible Variability Factors": [sop.possible_variability_factors],
            "References": [sop.references]
        }

        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode('utf-8')
    
    if st.button("Back"):
                st.experimental_rerun()
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
