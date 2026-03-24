# 해당 파일은 ipynb 에서 수정되었습니다.

# python import library
import pandas as pd
import numpy as np

# 파일 불러오기
df = pd.read_csv('../101_DT_1B040M1_1_20260319054822.csv', encoding='cp949')

# 1. 필요 없는 항목 삭제
df.drop(columns='단위', 'Unnamed: 6', '항목'], inplace=True)
df['나이추출'] = df['연령별'].str.extract(r'(\d+)').astype(float)
'''
df['연령별'].str    : 해당 columns 의 값을 문자열로 취급
.extract(r'(\d+)') : 정규 표현식을 사용하여 패턴 찾기. \d : 숫자
-> r'(\d+)' 형식으로 작성하는 이유 - 파이썬 버전이 높아지면서 \d 만 작성했을때, 코드는 잘 작동 하지만
                                   해당 문장에 쓰인 표현이 문자열인지 정규표현식인지
                                   모호하다 판단하여 주의 문구가 뜸.
.astype(float)     : 뽑아낸 패턴을 실수 타입으로 변환
'''

# 12번 줄의 작업으로 봅아낸 데이터를 정해진 범위 내 부분을 선택
df = df[~((df['나이추출'] >= 0) & (df['나이추출'] <= 19))]

# 선택한 데이터 삭제
df.drop(columns=['나이추출'], inplace=True)


# 2. 방대한 데이터 통합 작업 : 지역
# 기존의 행정구역 이름 끝 비교. 지정한 단어 포함 시, 시도 단위 판단. 없다면 None 반환
def Identify_sido(name):
  if name.endswith(('특별시', '광역시', '특별자치시', '도', '특별자치도')):
    return name
  return None

# 새로운 칼럼 이름 '시도', 해당 데이터 부분은 기존 행정구역(시군구)별에서 추출
df['시도'] = df['행정구역(시군구)별'].apply(Identify_sido)

# .ffill() 으로, 새 칼럼 빈칸을 앞 전의 이름으로 채움
df['시도'] = df['시도'].ffill()

# 원래 칼럼의 이름 renamed
df['시군구'] = df['행정구역(시군구)별']
df['인구수'] = df['2025 년']

# 시도, 시군구가 같은 행과 전국 데이터 제거, 단, 세종특별자치시일 경우 제외.
modifi_data = df[((df['시도'] != df['시군구'] | (df['시도'] == '세종특별자치시')) &
                  (df['시군구'] != 전국)].copy()

# 칼럼 재정렬
modifi_data = modifi_data[['시도', '시군구', '성별', '연령별', '인구수']]


# 3. 방대한 데이터 통합 작업 : 나이
modifi_data['나이'] = modifi_data['연령별'].str.extract(r'(\d)').astype(float)
modifi_data = modifi_data.dropna(subset=['나이']).copy()

# 나이시작점과 나이끝점 지정
s_age = (modifi_data['나이'] // 5 * 5).astype(int)
e_age = (s_age + 4).astype(int)

# 연령대 묶기
modifi_data['연령대'] = s_age.astype(str) + '~' + e_age.astype(str) + "세"
df_pivot = modifi_data.pivot_table(
  index=['시도', '시군구', '성별],
  columns='연령대',
  values='인구수',
  aggfunc='sum'
).reset_index()
df_pivot.fillna(0, inplace=True)

# lambda 활용 columns 재배치
fixed_cols = ['시도', '시군구', '성별']
age_cols = [c for c in df_pivot.columns if c not in fixed_cols]

# 나이 columns에서 ~ 뒤를 제외 하고 계산. 즉, 20~24세 부분에서 20만 처리
age_cols.sort(key=lambda x: int(x.split('~')[0]))

# 합치기
df_pivot = df_pivot[fixed_cols + age_cols]


# 4. 파일 저장
df_pivot.to_csv('../Modifi_Data.csv', index=False, encoding='utf-8)
