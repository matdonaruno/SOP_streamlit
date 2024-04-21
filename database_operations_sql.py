from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import JSON
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta


logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

JST = timezone(timedelta(hours=+9))

Base = declarative_base()

class Facility(Base):
    __tablename__ = 'facilities'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class SOPDetail(Base):
    __tablename__ = 'sop_details'
    id = Column(Integer, primary_key=True)
    edited_sop_id = Column(Integer, ForeignKey('edited_sops.id'))
    edited_sop = relationship("EditedSOP", back_populates="sop_detail")

    main_title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    revision_history = Column(Text, nullable=False)
    # 新しい属性の追加
    measurement_method = Column(Text)
    measurement_principle = Column(Text)
    parameters = Column(Text)
    linearity = Column(Text)
    accuracy = Column(Text)
    reproducibility = Column(Text)
    limit_of_quantitation = Column(Text)
    instrument_difference = Column(Text)
    sample_type = Column(Text)
    sample_storage = Column(Text)
    patient_preparation = Column(Text)
    container_and_additives = Column(Text)
    measuring_instrument = Column(Text)
    equipment_and_tools = Column(Text)
    reagents_and_composition = Column(Text)
    reagent_preparation = Column(Text)
    reagent_storage_and_expiry = Column(Text)
    sampling_amount = Column(Text)
    required_volume = Column(Text)
    environment = Column(Text)
    safety_management = Column(Text)
    standard_solution_preparation_and_storage = Column(Text)
    calibration_curve = Column(Text)
    result_judgement = Column(Text)
    calibration_implementation = Column(Text)
    traceability = Column(Text)
    operation_steps = Column(Text)
    accuracy_control_sample_preparation_and_storage = Column(Text)
    internal_accuracy_management = Column(Text)
    accuracy_control_tolerance = Column(Text)
    external_accuracy_management = Column(Text)
    interference_and_cross_reactivity = Column(Text)
    analysis_result_calculation_method = Column(Text)
    measurement_uncertainty = Column(Text)

    instructions_for_determining_quantitative_results_outside_the_measurement_range = Column(Text)
    reinspection_criteria = Column(Text)
    data_selection_criteria_for_reinspection = Column(Text)
    alert_values_and_critical_values = Column(Text)
    clinical_significance = Column(Text)
    related_items = Column(Text)
    possible_variability_factors = Column(Text)

    references = Column(Text)
    created_at = Column(DateTime, default=datetime.now(JST))

class EditedSOP(Base):
    __tablename__ = 'edited_sops'
    id = Column(Integer, primary_key=True)
    sop_id = Column(Integer, ForeignKey('sop_details.id'), nullable=False)

    main_title = Column(String, nullable=False)
    subtitle = Column(String, nullable=False)
    revision_history = Column(Text, nullable=False)

    # 新しい属性の追加
    measurement_method = Column(Text)
    measurement_principle = Column(Text)
    parameters = Column(Text)
    linearity = Column(Text)
    accuracy = Column(Text)
    reproducibility = Column(Text)
    limit_of_quantitation = Column(Text)
    instrument_difference = Column(Text)
    sample_type = Column(Text)
    sample_storage = Column(Text)
    patient_preparation = Column(Text)
    container_and_additives = Column(Text)
    measuring_instrument = Column(Text)
    equipment_and_tools = Column(Text)
    reagents_and_composition = Column(Text)
    reagent_preparation = Column(Text)
    reagent_storage_and_expiry = Column(Text)
    sampling_amount = Column(Text)
    required_volume = Column(Text)
    environment = Column(Text)
    safety_management = Column(Text)
    standard_solution_preparation_and_storage = Column(Text)
    calibration_curve = Column(Text)
    result_judgement = Column(Text)
    calibration_implementation = Column(Text)
    traceability = Column(Text)
    operation_steps = Column(Text)
    accuracy_control_sample_preparation_and_storage = Column(Text)
    internal_accuracy_management = Column(Text)
    accuracy_control_tolerance = Column(Text)
    external_accuracy_management = Column(Text)
    interference_and_cross_reactivity = Column(Text)
    analysis_result_calculation_method = Column(Text)
    measurement_uncertainty = Column(Text)

    instructions_for_determining_quantitative_results_outside_the_measurement_range = Column(Text)
    reinspection_criteria = Column(Text)
    data_selection_criteria_for_reinspection = Column(Text)
    alert_values_and_critical_values = Column(Text)
    clinical_significance = Column(Text)
    related_items = Column(Text)
    possible_variability_factors = Column(Text)

    references = Column(Text)
    created_at = Column(DateTime, default=datetime.now(JST))
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    creator_editor = Column(String)
    creator_editor_timestamp = Column(DateTime, default=lambda: datetime.now(JST))
    approver = Column(String)
    approver_timestamp = Column(DateTime, default=lambda: datetime.now(JST))
    document_manager = Column(String)
    document_manager_timestamp = Column(DateTime, default=lambda: datetime.now(JST))
    own_revision_history = Column(Text)
    facility = relationship("Facility", back_populates="edited_sops")
    sop_detail = relationship("SOPDetail", back_populates="edited_sop")
    
class DepartmentalSOP(Base):
    __tablename__ = 'departmental_sops'
    id = Column(Integer, primary_key=True)
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    department_title = Column(String, nullable=False)
    details = Column(JSON)  # 部門別SOPの詳細情報を格納するJSONカラム
    created_at = Column(DateTime, default=datetime.now(JST))
    updated_at = Column(DateTime, default=datetime.now(JST))

    facility = relationship("Facility")  # Facilityクラスへの参照

class EditDepartmentalSOP(Base):
    __tablename__ = 'edit_departmental_sops'
    id = Column(Integer, primary_key=True)
    departmental_sop_id = Column(Integer, ForeignKey('departmental_sops.id'))
    edited_by = Column(String, nullable=False)
    edit_timestamp = Column(DateTime, default=datetime.now(JST))
    details = Column(JSON)  # 編集されたSOPの詳細情報を格納するJSONカラム

    departmental_sop = relationship("DepartmentalSOP")  # DepartmentalSOPクラスへの参照

class EditEquipmentSOP(Base):
    __tablename__ = 'edit_equipment_sops'
    id = Column(Integer, primary_key=True)
    equipment_sop_id = Column(Integer, ForeignKey('equipment_sops.id'))  # 修正: 正しい外部キー指定
    edited_by = Column(String, nullable=False)
    edit_timestamp = Column(DateTime, nullable=False)
    details = Column(JSON)  # JSON型で詳細を保存

    equipment_sop = relationship("EquipmentSOP", back_populates="edit_sops")  # relationshipを設定

class EquipmentSOP(Base):
    __tablename__ = 'equipment_sops'
    id = Column(Integer, primary_key=True)
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    equipment_name = Column(String, nullable=False)
    details = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    edit_sops = relationship("EditEquipmentSOP", back_populates="equipment_sop")  # 追加: EditEquipmentSOPとのリレーション



# 既存の関係を更新
SOPDetail.edited_sops = relationship("EditedSOP", back_populates="sop_detail", cascade="all, delete, delete-orphan")
Facility.edited_sops = relationship("EditedSOP", order_by=EditedSOP.id, back_populates="facility")


class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    id = Column(Integer, primary_key=True)
    sop_id = Column(Integer, ForeignKey('sop_details.id'), nullable=False)
    file_name = Column(String, nullable=False)
    file_content = Column(Text, nullable=False)
    revision_history = Column(Text)
    registrant_id = Column(Integer)
    registered_at = Column(DateTime, default=datetime.now(JST))

    sop_detail = relationship("SOPDetail", back_populates="uploaded_files")

SOPDetail.uploaded_files = relationship("UploadedFile", back_populates="sop_detail", cascade="all, delete, delete-orphan")


engine = create_engine('sqlite:///sop_database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class UncertaintyFactorDiagram(Base):
    __tablename__ = 'uncertainty_factor_diagrams'
    id = Column(Integer, primary_key=True)
    sop_id = Column(Integer, ForeignKey('sop_details.id'), nullable=False)
    diagram_name = Column(String, nullable=False)
    diagram_data = Column(LargeBinary, nullable=False)
    registered_at = Column(DateTime, default=datetime.now(JST))

    sop_detail = relationship("SOPDetail", back_populates="uncertainty_factor_diagrams")

SOPDetail.uncertainty_factor_diagrams = relationship("UncertaintyFactorDiagram", back_populates="sop_detail", cascade="all, delete, delete-orphan")


def check_sop_exists(main_title, subtitle):
    session = Session()
    exists = session.query(SOPDetail).filter(SOPDetail.main_title == main_title, SOPDetail.subtitle == subtitle).first()
    session.close()
    return exists is not None

def initialize_database():
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Failed to create database schema: {e}")

def save_sop_to_database(main_title, subtitle, revision_history, sections_content):
    session = Session()
    try:
        # Check if a record with the same MainTitle, SubTitle, and Revision History already exists
        existing_record = session.query(SOPDetail).filter(
            SOPDetail.main_title == main_title,
            SOPDetail.subtitle == subtitle,
            SOPDetail.revision_history == revision_history
        ).first()

        if existing_record:
            print(f"A record with the same details already exists with ID: {existing_record.id}")
            return None

        sop_detail = SOPDetail(
            main_title=main_title,
            subtitle=subtitle,
            revision_history=revision_history,
            measurement_method=sections_content.get("測定法", ""),
            measurement_principle=sections_content.get("測定原理", ""),
            parameters=sections_content.get("パラメーター", ""),
            linearity=sections_content.get("直進性", ""),
            accuracy=sections_content.get("正確性", ""),
            reproducibility=sections_content.get("同時再現性", ""),
            limit_of_quantitation=sections_content.get("定量下限", ""),
            instrument_difference=sections_content.get("機器間差", ""),
            sample_type=sections_content.get("サンプルの種類", ""),
            sample_storage=sections_content.get("サンプルの貯法", ""),
            patient_preparation=sections_content.get("患者準備", ""),
            container_and_additives=sections_content.get("容器および添加剤の種類", ""),
            measuring_instrument=sections_content.get("測定機器", ""),
            equipment_and_tools=sections_content.get("必要な機材および器具", ""),
            reagents_and_composition=sections_content.get("試薬および構成", ""),
            reagent_preparation=sections_content.get("試薬の調整", ""),
            reagent_storage_and_expiry=sections_content.get("試薬保管条件および有効期限", ""),
            sampling_amount=sections_content.get("サンプリング量", ""),
            required_volume=sections_content.get("必要量", ""),
            environment=sections_content.get("環境", ""),
            safety_management=sections_content.get("安全管理", ""),
            standard_solution_preparation_and_storage=sections_content.get("標準液の調整および保管条件", ""),
            calibration_curve=sections_content.get("検量線", ""),
            result_judgement=sections_content.get("結果の判定", ""),
            calibration_implementation=sections_content.get("校正の実施", ""),
            traceability=sections_content.get("トレーサビリティ", ""),
            operation_steps=sections_content.get("操作ステップ", ""),
            accuracy_control_sample_preparation_and_storage=sections_content.get("精度管理試料の調整および保管条件", ""),
            internal_accuracy_management=sections_content.get("内部精度管理", ""),
            accuracy_control_tolerance=sections_content.get("精度管理許容限界", ""),
            external_accuracy_management=sections_content.get("外部精度管理", ""),
            interference_and_cross_reactivity=sections_content.get("干渉および交差反応", ""),
            analysis_result_calculation_method=sections_content.get("分析結果の計算法", ""),
            measurement_uncertainty=sections_content.get("測定の不確かさ", ""),
            
            instructions_for_determining_quantitative_results_outside_the_measurement_range=sections_content.get("結果が測定範囲外であった場合の定量結果決定に関する指示", ""),
            reinspection_criteria=sections_content.get("再検基準", ""),
            data_selection_criteria_for_reinspection=sections_content.get("再検時のデータ選択基準", ""),
            alert_values_and_critical_values=sections_content.get("警戒値・緊急異常値", ""),
            clinical_significance=sections_content.get("臨床的意義", ""),
            related_items=sections_content.get("関連項目", ""),
            possible_variability_factors=sections_content.get("可能性のある変動要因", ""),
            references=sections_content.get("参考資料", "")
        )

        session.add(sop_detail)
        session.commit()
        print(f"SOP Detail saved with ID: {sop_detail.id}")
        return sop_detail.id

    except SQLAlchemyError as e:
        print(f"Error saving SOP Detail: {e}")
        session.rollback()
        return None

def edit_sop_details(
    sop_id, 
    main_title, 
    subtitle, 
    revision_history, 
    measurement_method, 
    measurement_principle, 
    parameters, 
    linearity, 
    accuracy, 
    reproducibility, 
    limit_of_quantitation, 
    instrument_difference, 
    sample_type, 
    sample_storage, 
    patient_preparation, 
    container_and_additives, 
    measuring_instrument, 
    equipment_and_tools, 
    reagents_and_composition, 
    reagent_preparation, 
    reagent_storage_and_expiry, 
    sampling_amount, 
    required_volume, 
    environment, 
    safety_management, 
    standard_solution_preparation_and_storage, 
    calibration_curve, 
    result_judgement, 
    calibration_implementation, 
    traceability, 
    operation_steps, 
    accuracy_control_sample_preparation_and_storage, 
    internal_accuracy_management, 
    accuracy_control_tolerance, 
    external_accuracy_management, 
    interference_and_cross_reactivity, 
    analysis_result_calculation_method, 
    measurement_uncertainty, 
    instructions_for_determining_quantitative_results_outside_the_measurement_range, 
    reinspection_criteria, 
    data_selection_criteria_for_reinspection, 
    alert_values_and_critical_values, 
    clinical_significance, 
    related_items, 
    possible_variability_factors, 
    references, 
    facility_id, 
    creator_editor, 
    approver, 
    document_manager, 
    own_revision_history,
    new_values=None  # 新しいまたは追加の編集が必要なフィールドの辞書
):
    session = Session()
    try:
        # EditedSOPテーブルの更新または新規作成
        edited_sop = session.query(EditedSOP).filter(EditedSOP.sop_id == sop_id).first()
        if not edited_sop:
            edited_sop = EditedSOP(sop_id=sop_id)
            session.add(edited_sop)

        # creator_editorが入力された場合のみタイムスタンプを更新
        if creator_editor is not None and creator_editor != "":
            edited_sop.creator_editor_timestamp = datetime.now(JST)

        # approverが入力された場合のみタイムスタンプを更新
        if approver is not None and approver != "":
            edited_sop.approver_timestamp = datetime.now(JST)

        # document_managerが入力された場合のみタイムスタンプを更新
        if document_manager is not None and document_manager != "":
            edited_sop.document_manager_timestamp = datetime.now(JST)


        # 以下のフィールドを更新
        fields_to_update = {
            'main_title': main_title,
            'subtitle': subtitle,
            'revision_history': revision_history,
            'measurement_method': measurement_method,
            'measurement_principle': measurement_principle,
            'parameters': parameters,
            'linearity': linearity,
            'accuracy': accuracy,
            'reproducibility': reproducibility,
            'limit_of_quantitation': limit_of_quantitation,
            'instrument_difference': instrument_difference,
            'sample_type': sample_type,
            'sample_storage': sample_storage,
            'patient_preparation': patient_preparation,
            'container_and_additives': container_and_additives,
            'measuring_instrument': measuring_instrument,
            'equipment_and_tools': equipment_and_tools,
            'reagents_and_composition': reagents_and_composition,
            'reagent_preparation': reagent_preparation,
            'reagent_storage_and_expiry': reagent_storage_and_expiry,
            'sampling_amount': sampling_amount,
            'required_volume': required_volume,
            'environment': environment,
            'safety_management': safety_management,
            'standard_solution_preparation_and_storage': standard_solution_preparation_and_storage,
            'calibration_curve': calibration_curve,
            'result_judgement': result_judgement,
            'calibration_implementation': calibration_implementation,
            'traceability': traceability,
            'operation_steps': operation_steps,
            'accuracy_control_sample_preparation_and_storage': accuracy_control_sample_preparation_and_storage,
            'internal_accuracy_management': internal_accuracy_management,
            'accuracy_control_tolerance': accuracy_control_tolerance,
            'external_accuracy_management': external_accuracy_management,
            'interference_and_cross_reactivity': interference_and_cross_reactivity,
            'analysis_result_calculation_method': analysis_result_calculation_method,
            'measurement_uncertainty': measurement_uncertainty,
            'instructions_for_determining_quantitative_results_outside_the_measurement_range': instructions_for_determining_quantitative_results_outside_the_measurement_range,
            'reinspection_criteria': reinspection_criteria,
            'data_selection_criteria_for_reinspection': data_selection_criteria_for_reinspection,
            'alert_values_and_critical_values': alert_values_and_critical_values,
            'clinical_significance': clinical_significance,
            'related_items': related_items,
            'possible_variability_factors': possible_variability_factors,
            'references': references,
            'facility_id': facility_id,
            'creator_editor': creator_editor,
            'approver': approver,
            'document_manager': document_manager,
            'own_revision_history': own_revision_history
        }


        for key, value in fields_to_update.items():
            setattr(edited_sop, key, value)

        if new_values:
            for key, value in new_values.items():
                if hasattr(edited_sop, key):
                    setattr(edited_sop, key, value)

        session.commit()
        return True, f"SOPが正常に更新されました。ID: {edited_sop.id}"

    except Exception as e:
        session.rollback()
        return False, f"更新に失敗しました。エラー: {e}"

    finally:
        session.close()

# データベースからSOPの一覧を取得する関数
def fetch_sop_list():
    session = Session()
    sop_list = session.query(SOPDetail).all()
    session.close()
    return sop_list

def save_new_facility_name_if_not_exists(new_facility_name):
    session = Session()
    facility = session.query(Facility).filter(Facility.name == new_facility_name).first()
    if not facility:
        facility = Facility(name=new_facility_name)
        session.add(facility)
        session.commit()
        print(f"新しい施設名 '{new_facility_name}' をデータベースに追加しました。")
    else:
        print(f"施設名 '{new_facility_name}' は既にデータベースに存在します。")
    return facility.id

def fetch_facility_id_by_name(facility_name):
    session = Session()
    try:
        facility = session.query(Facility).filter_by(name=facility_name).first()
        if facility:
            return facility.id
        else:
            return None
    except Exception as e:
        print(f"Error fetching facility ID by name: {e}")
        return None
    finally:
        session.close()

def fetch_facility_names_from_database() -> List[str]:
    session = Session()
    try:
        # データベースから施設の全リストを取得
        facilities = session.query(Facility).all()
        # 施設名のリストを作成
        facility_names = [facility.name for facility in facilities]
        return facility_names

    except SQLAlchemyError as e:
        # データベースクエリ中にエラーが発生した場合、エラーメッセージを出力
        print(f"Error fetching facility names from database: {e}")
        return []  # エラーが発生した場合は空のリストを返す

    finally:
        # セッションを閉じる
        session.close()

def add_departmental_sop(facility_id, department_title, details):
    session = Session()
    try:
        # 重複チェック
        existing_sop = session.query(DepartmentalSOP).filter_by(facility_id=facility_id, department_title=department_title).first()
        if existing_sop:
            return None, "同じ部門で同じタイトルのSOPが既に存在します。"

        new_sop = DepartmentalSOP(
            facility_id=facility_id,
            department_title=department_title,
            details=details
        )
        session.add(new_sop)
        session.commit()
        return new_sop.id, "SOPが正常に追加されました。"
    except SQLAlchemyError as e:
        session.rollback()
        # エラーメッセージをロギングする（実際のアプリケーションでは、より具体的なロギング手法を用いる）
        print(f"データベース操作中にエラーが発生しました: {e}")
        return None, "SOPの追加中にエラーが発生しました。"

def add_equipment_sop(facility_id, equipment_name, details):
    session = Session()
    try:
        # 重複チェック
        existing_sop = session.query(EditEquipmentSOP).filter_by(facility_id=facility_id, equipment_name=equipment_name).first()
        if existing_sop:
            return None, "同じ機器名のSOPが既に存在します。"

        new_sop = EditEquipmentSOP(
            facility_id=facility_id,
            equipment_name=equipment_name,
            details=details
        )
        session.add(new_sop)
        session.commit()
        return new_sop.id, "機器SOPが正常に追加されました。"
    except SQLAlchemyError as e:
        session.rollback()
        print(f"データベース操作中にエラーが発生しました: {e}")
        return None, "機器SOPの追加中にエラーが発生しました。"
    finally:
        session.close()

def fetch_departmental_sops_by_facility(facility_id):
    session = Session()
    try:
        sops = session.query(DepartmentalSOP).filter(DepartmentalSOP.facility_id == facility_id).all()
        return sops, None  # エラーがない場合は、SOPリストと共にNoneを返す
    except SQLAlchemyError as e:
        print(f"データベース操作中にエラーが発生しました: {e}")
        return [], f"部門別SOPの取得中にエラーが発生しました。"  # エラーが発生した場合は、空のリストとエラーメッセージを返す
    finally:
        session.close()

def fetch_equipment_sops_by_facility(facility_id):
    session = Session()
    try:
        sops = session.query(EditEquipmentSOP).filter(EditEquipmentSOP.facility_id == facility_id).all()
        return sops, None  # エラーがない場合は、SOPリストと共にNoneを返す
    except SQLAlchemyError as e:
        print(f"データベース操作中にエラーが発生しました: {e}")
        return [], f"部門別SOPの取得中にエラーが発生しました。"  # エラーが発生した場合は、空のリストとエラーメッセージを返す
    finally:
        session.close()

def get_departmental_sop_details(departmental_sop_id: int) -> Optional[dict]:
    """
    指定された部門SOPの詳細をデータベースから取得します。

    Parameters:
    - departmental_sop_id (int): 取得したい部門SOPのID。

    Returns:
    - dict: 部門SOPの詳細を含む辞書。
    - None: SOPが見つからない場合やデータベース操作に失敗した場合。
    """
    session = Session()
    try:
        # 指定されたIDの部門SOPの詳細を取得
        departmental_sop = session.query(DepartmentalSOP).get(departmental_sop_id)
        if departmental_sop:
            return departmental_sop.details
        else:
            return None  # 指定されたIDのSOPが存在しない場合
    except SQLAlchemyError as e:
        print(f"Error fetching departmental SOP details from database: {e}")
        return None
    finally:
        session.close()

def get_equipment_sop_details(equipment_sop_id: int):
    session = Session()
    try:
        # 指定されたIDの機器SOPの詳細を取得
        equipment_sop = session.query(EditEquipmentSOP).get(equipment_sop_id)
        if equipment_sop:
            # SOPの詳細が存在する場合は、詳細を返す
            return equipment_sop.details
        else:
            # 指定されたIDのSOPが存在しない場合は、Noneを返す
            return None
    except SQLAlchemyError as e:
        # データベース操作中にエラーが発生した場合
        print(f"Error fetching equipment SOP details from database: {e}")
        return None
    finally:
        # セッションを閉じる
        session.close()

def update_departmental_sop(sop_id, updated_details, editor_name):
    session = Session()
    try:
        # 既存のSOPデータを取得
        departmental_sop = session.query(DepartmentalSOP).get(sop_id)
        if not departmental_sop:
            return False, "SOP not found"

        # 新しい編集履歴レコードを作成
        edit_sop = EditDepartmentalSOP(
            departmental_sop_id=sop_id,
            edited_by=editor_name,
            details=updated_details
        )
        session.add(edit_sop)
        
        # 既存のSOPデータを更新
        departmental_sop.details = updated_details
        
        session.commit()
        return True, "SOP updated successfully"
    except SQLAlchemyError as e:
        session.rollback()
        print(f"データベース操作中にエラーが発生しました: {e}")
        return False, "Error updating SOP"
    finally:
        session.close()

def update_equipment_sop(sop_id, updated_details, editor_name):
    session = Session()
    try:
        # 既存のSOPデータを取得
        equipment_sop = session.query(EditEquipmentSOP).get(sop_id)
        if not equipment_sop:
            return False, "SOP not found"

        # 新しい編集履歴レコードを作成
        edit_sop = EditEquipmentSOP(
            equipment_sop_id=sop_id,
            edited_by=editor_name,
            details=updated_details
        )
        session.add(edit_sop)
        
        # 既存のSOPデータを更新
        equipment_sop.details = updated_details
        
        session.commit()
        return True, "SOP updated successfully"
    except SQLAlchemyError as e:
        session.rollback()
        print(f"データベース操作中にエラーが発生しました: {e}")
        return False, "Error updating SOP"
    finally:
        session.close()

def check_departmental_sop_exists(facility_id, department_title):
    session = Session()
    try:
        # 施設IDと部門タイトルでフィルタリングし、最初の結果を取得
        existing_sop = session.query(DepartmentalSOP).filter(
            DepartmentalSOP.facility_id == facility_id,
            DepartmentalSOP.department_title == department_title
        ).first()

        # SOPが存在する場合はTrue、そうでない場合はFalseを返す
        return existing_sop is not None

    except SQLAlchemyError as e:
        print(f"データベース検索中にエラーが発生しました: {e}")
        return False

    finally:
        session.close()

def fetch_edited_sops_by_facility_name(facility_name: str) -> Tuple[List[dict], Optional[str]]:
    session = Session()
    try:
        facility = session.query(Facility).filter_by(name=facility_name).first()
        if facility:
            edited_sops = session.query(EditedSOP).filter_by(facility_id=facility.id).all()
            return [sop_to_dict(sop) for sop in edited_sops], None
        else:
            return [], "Specified facility does not exist."
    except SQLAlchemyError as e:
        return [], f"Database error occurred while fetching SOPs: {e}"
    finally:
        session.close()

def sop_to_dict(sop):
    """
    EditedSOPオブジェクトを辞書に変換します。
    """
    return {
        'id': sop.id,
        'facility_id': sop.facility_id,
        'sop_detail': sop.sop_detail,
        'editor_name': sop.editor_name,
        'edit_timestamp': sop.edit_timestamp
    }
