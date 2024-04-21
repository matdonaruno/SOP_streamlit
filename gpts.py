# gpt.py
import openai
from dotenv import load_dotenv
import os
from database_operations_sql import Session, Facility, EditedSOP

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def fetch_sop_by_facility(selected_facility_name):
    session = Session()
    # Facility テーブルから施設IDを取得
    facility = session.query(Facility).filter(Facility.name == selected_facility_name).first()
    if facility:
        # EditedSOP テーブルから施設IDに基づくSOPの内容を取得
        sop = session.query(EditedSOP).filter(EditedSOP.facility_id == facility.id).first()
        if sop:
            # SOPの内容（ここでは例としてpurposeフィールドを使用）を返す
            session.close()
            return sop.purpose  # 必要に応じて他のフィールドに変更
    session.close()
    return ""

# 修正後のコード（v1/chat/completions エンドポイントを使用）
def ask_gpt(sop_content, question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # または使用しているモデルに応じて変更
        messages=[
            {"role": "system", "content": sop_content},
            {"role": "user", "content": question}
        ],
        temperature=0.5,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response.choices[0].message['content']


