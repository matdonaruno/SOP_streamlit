import streamlit as st
import pandas as pd
from database_operations_sql import fetch_edited_sops_by_facility_name

def show_sop_descriptions(selected_facility_name):
    edited_sops = fetch_edited_sops_by_facility_name(selected_facility_name)
    # データをデータフレームに変換
    data = []
    for edited_sop in edited_sops:
      sop_data = {
          "Main Title": edited_sop.main_title,
          "Sub Title": edited_sop.subtitle,
          "Revision History": edited_sop.revision_history,
          "測定法": edited_sop.measurement_method,
          "測定原理": edited_sop.measurement_principle,
          "パラメーター": edited_sop.parameters,
          "直進性": edited_sop.linearity,
          "正確性": edited_sop.accuracy,
          "同時再現性": edited_sop.reproducibility,
          "定量下限": edited_sop.limit_of_quantitation,
          "機器間差": edited_sop.instrument_difference,
          "サンプルの種類": edited_sop.sample_type,
          "サンプルの保管方法": edited_sop.sample_storage,
          "患者準備": edited_sop.patient_preparation,
          "容器および添加剤の種類": edited_sop.container_and_additives,
          "測定機器": edited_sop.measuring_instrument,
          "必要な機材および器具": edited_sop.equipment_and_tools,
          "試薬および構成": edited_sop.reagents_and_composition,
          "試薬の調整": edited_sop.reagent_preparation,
          "試薬保管条件および有効期限": edited_sop.reagent_storage_and_expiry,
          "サンプリング量": edited_sop.sampling_amount,
          "必要量": edited_sop.required_volume,
          "環境": edited_sop.environment,
          "安全管理": edited_sop.safety_management,
          "標準液の調整および保管条件": edited_sop.standard_solution_preparation_and_storage,
          "検量線": edited_sop.calibration_curve,
          "結果の判定": edited_sop.result_judgement,
          "校正の実施": edited_sop.calibration_implementation,
          "トレーサビリティ": edited_sop.traceability,
          "操作ステップ": edited_sop.operation_steps,
          "精度管理試料の調整および保管条件": edited_sop.accuracy_control_sample_preparation_and_storage,
          "内部精度管理": edited_sop.internal_accuracy_management,
          "精度管理許容限界": edited_sop.accuracy_control_tolerance,
          "外部精度管理": edited_sop.external_accuracy_management,
          "干渉および交差反応": edited_sop.interference_and_cross_reactivity,
          "分析結果の計算法": edited_sop.analysis_result_calculation_method,
          "測定の不確かさ": edited_sop.measurement_uncertainty,

          "結果が測定範囲外であった場合の定量結果決定に関する指示": edited_sop.instructions_for_determining_quantitative_results_outside_the_measurement_range,
          "再検基準": edited_sop.reinspection_criteria,
          "再検時のデータ選択基準": edited_sop.data_selection_criteria_for_reinspection,
          "警戒値・緊急異常値": edited_sop.alert_values_and_critical_values,
          "臨床的意義": edited_sop.clinical_significance,
          "関連項目": edited_sop.related_items,
          "可能性のある変動要因": edited_sop.possible_variability_factors,
          "作成者/編集者": edited_sop.creator_editor,
          "認証者": edited_sop.approver,
          "文書管理者": edited_sop.document_manager,
          "版数（改版履歴）": edited_sop.own_revision_history,
          "登録日": edited_sop.created_at
      }

      data.append(sop_data)
      # "不確かさの要因図" が存在する場合には画像として表示
      if edited_sop.uncertainty_factor_diagram:
          st.subheader(f"{edited_sop.main_title} - 不確かさの要因図")
          st.image(edited_sop.uncertainty_factor_diagram, caption="不確かさの要因図")

    df = pd.DataFrame(data)
    return df
