from flask import Flask, session, render_template, request
from datetime import datetime
import os, re, pymysql
from dotenv import load_dotenv #env 로딩 라이브러리

# env 파일 불러오기
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_KEY') # 세션 암호화 키 생성

# db 연결 정보 변수에 할당
db_conn = {
    'host' : os.getenv('DB_HOST'),
    'port' : 3306,
    'user' : os.getenv('DB_USER'),
    'password' : os.getenv('DB_PW'),
    'charset' : 'utf8'
}

# 데이터베이스를 불러오는 함수
def load_db(): 
    conn = pymysql.connect(**db_conn) # **을 사용하여 키:값 자동 할당
    cur = conn.cursor()
    
    # users 데이터베이스 없으면 생성
    sql_user_db = "CREATE DATABASE IF NOT EXISTS users" 
    cur.execute(sql_user_db)

    # 데이터 베이스안의 테이블 (users.user)이 없을때 생성하기
    sql_user_table = """
    CREATE TABLE IF NOT EXISTS users.user_data( 
        number INT AUTO_INCREMENT PRIMARY KEY, 
        userid VARCHAR(15) NOT NULL UNIQUE,
        userpw VARCHAR(30) NOT NULL
    )
    """
    cur.execute(sql_user_table)

    sql_studyroom = "CREATE DATABASE IF NOT EXISTS study"
    cur.execute(sql_studyroom)

    sql_room = """
    CREATE TABLE IF NOT EXISTS study.room(
        room INT NOT NULL,
        name VARCHAR(15) NOT NULL,
        date DATETIME NOT NULL
    )
    """
    cur.execute(sql_room)

    conn.commit() # DB에 저장
    conn.close()


# 회원가입 아이디 중복을 방지하기 위한 함수
def sign_up_check(id):
    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    userid = id
    sql_find_id = "SELECT userid FROM users.user_data WHERE userid = %s"
    cur.execute(sql_find_id, (userid,)) # execute는 튜플 값을 다뤄서 (userid,)로 사용
    result = cur.fetchone()  # fetchone은 데이터가 없다면 None 반환

    conn.close()

    if result == None: 
        print("중복 계정이 없습니다.")
        return True
    else:
        print("중복 계정이 존재합니다.")
        return False    


# 로그인 계정 중복을 방지하기 위한 함수
def login_check(id,pw):
    userid = id
    userpw = pw

    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    sql_find_idpw = """
    SELECT userid,userpw FROM users.user_data 
    WHERE userid = %s AND userpw = %s
    """

    cur.execute(sql_find_idpw,(userid,userpw))
    result = cur.fetchone()

    conn.close()

    # 반환값이 None 즉 계정이 DB에 없을때
    if result == None:
        print("로그인 실패")
        return False
    else:
        print("로그인 성공")
        return True
    

# DB에 유저를 추가히는 함수
def create_user(id,pw):
    input_id = id
    input_pw = pw

    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    sql_input = """
    INSERT INTO users.user_data (userid, userpw) VALUES (%s, %s)
    """

    cur.execute(sql_input,(input_id, input_pw))
    conn.commit()
    conn.close()
    print("계정 생성 완료!")


# 예약 날짜 형식이 올바른지 확인하는 함수
def date_set(s_date):
    start = s_date

    # 문자열을 datetime 객체로 변환해 값이 올바른지 확인
    try:
        start = datetime.strptime(start,"%Y.%m.%d")
    except:
        return False
    else:   
        return True 


# 스크립트로 메세지창과 사이트 이동을 구현해둔 함수
def message(msg, url):
    return f"""
    <script>
    alert('{msg}')
    window.location.href = '{url}';
    </script>
    """

# 스터디룸을 예약해주는 함수
def input_res_data(room, id ,date):
    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    result = res_check(room, date)

    if result == True:
        sql_res_room = """
        INSERT INTO study.room (room, name, date) VALUES (%s, %s, %s)    
        """
        cur.execute(sql_res_room,(room, id, date))
        conn.commit()
        conn.close()

        return True
    else:
        return False


# 방의 중복 여부를 확인하는 함수
def res_check(room, date):
    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    sql = """ 
    SELECT room, date FROM study.room WHERE room = %s and date = %s;
    """

    cur.execute(sql,(room,date))
    result = cur.fetchone()

    if result == None:
        return True
    else:
        return False


def show_res():
    conn = pymysql.connect(**db_conn)
    cur = conn.cursor()

    sql_show_res = """
    SELECT room,date FROM study.room WHERE name = %s
    """

    cur.execute(sql_show_res,(session['userid'],))
    result = cur.fetchall()

    conn.close()

    return result


@app.route('/')  # 메인 페이지 경로
def main():
    return render_template('main.html') # template 폴더안의 파일 브라우저에 출력



@app.route('/login', methods = ['GET','POST']) 
def login():
    if request.method == 'POST':
        userid = request.form['id']
        userpw = request.form['pw']

        result = login_check(userid, userpw)

        if result == True:
            session['userid'] = userid # 사용자에게 세션 값 부여
            return message('로그인 완료','/')
        else:
            return message('존재하지 않는 계정입니다','/login')
        

    return render_template('login.html')



@app.route('/reservation', methods = ['GET','POST'])
def resvation():
    if 'userid' not in session:
        return message('예약은 로그인 후 이용이 가능합니다.','/login')
    
    if request.method == 'POST':
        room_number = request.form['room_number']
        res_date_s = request.form['res_date_s']

        if room_number not in ['1','2','3','4']:
            return message('1 ~ 4 사이의 방을 선택해주세요','/reservation')
        
        if date_set(res_date_s) == True:
            status = input_res_data(room_number, session['userid'] ,res_date_s)

            if status == True:
                return message('예약이 완료되었습니다!','/')
            else:
                return message('이미 예약된 방입니다.','/reservation')   
                  
        else:
            return message('입력 형식이 잘못되었습니다','/reservation')

    return render_template('reservation.html')

@app.route('/reservation_check', methods = ['GET'])
def reservation_check():
    result = show_res()
    msg = f"{session['userid']}님 예약 내역입니다\\n\\n" # js는 줄바꿈을 허용하지 않아 \\n 를 사용

    for i in result:
        room = str(i[0])
        date = str(i[1])
        msg += f'예약 방 번호: {room}  예약 날짜: {date}\\n'

    return message(msg,'/reservation')


@app.route('/signup', methods = ['GET','POST'])
def sign_up():
    if request.method == "POST":
        userid = request.form['user_id']
        userpw = request.form['user_pw']

        if " " in userid or " " in userpw:
            return message('공백없이 생성해주세요','/signup')
        
        if not (len(userid) <= 15 and len(userpw) <= 30):
            return message('아이디는 15자 비밀번호는 30자 이하로 생성해주세요','/signup')

        if not re.fullmatch(r"[A-Za-z0-9]+", userid) or not re.fullmatch(r"[A-Za-z0-9!@]+", userpw):
            return message('아이디는 영어, 숫자 비밀번호는 영어, 숫자, !, @ 만 사용 가능합니다','/signup')
           
        result = sign_up_check(userid)
        if result == True:
            create_user(userid, userpw)
            print(f"id:{userid} / pw:{userpw}")
            return message('회원가입이 완료되었습니다','/login')
        else:
            print("생성 실패")
            print(f"id:{userid} / pw:{userpw}")
            return message('이미 존재하는 아이디입니다','/signup')
    return render_template('sign_up.html')


if __name__ == '__main__':
    load_db()
    app.run(host='0.0.0.0', debug=False) 
