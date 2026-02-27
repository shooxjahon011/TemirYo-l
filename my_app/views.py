import PyPDF2
import docx
import csv
import openpyxl
from datetime import datetime, timezone
from django.db.models import  Sum
from django.http import HttpResponse,JsonResponse
from django.shortcuts import  redirect,render
from django.templatetags.static import static
from django.middleware.csrf import get_token
from .models import  ChatMessage, WorkSchedule , LocationHistory
from datetime import timedelta, date
from my_app.models import UserProfile, IshchiGuruh ,Otryad
from django.utils import timezone
from django.db.models import Q
import json
def get_single_location(request, worker_id):
    worker = UserProfile.objects.filter(id=worker_id).first()
    if worker:
        return JsonResponse({
            'lat': worker.lat,
            'lng': worker.lng,
            'is_working': worker.is_working,
            'name': worker.full_name or worker.login
        })
    return JsonResponse({'error': 'Topilmadi'}, status=404)
def toggle_work(request):
    if request.method == "POST":
        user_login = request.session.get('user_login')
        user = UserProfile.objects.filter(login=user_login).first()

        if not user:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

        action = request.POST.get('action')
        if action == 'start':
            user.is_working = True
            user.work_start_time = timezone.now()
        else:
            user.is_working = False
            # Ish tugaganda vaqtni nolga tushirish ixtiyoriy

        user.save()
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'invalid method'}, status=400)
def baxtsiz_hodisa(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    user = UserProfile.objects.filter(login=user_login).first()
    # ENDI ADMIN EMAS, IS_BOSS BO'LSA RUXSAT BERAMIZ
    is_boss = getattr(user, 'is_boss', False)

    video_url = static('uzb.mp4')

    # POST: Boss xabar yuborishi
    if request.method == "POST" and is_boss:
        fayl = request.FILES.get('admin_file')
        text_input = request.POST.get('text', '')
        final_content = text_input + "\n"

        if fayl:
            ext = fayl.name.split('.')[-1].lower()
            try:
                if ext == 'pdf':
                    reader = PyPDF2.PdfReader(fayl)
                    for page in reader.pages: final_content += page.extract_text() + "\n"
                elif ext in ['doc', 'docx']:
                    doc = docx.Document(fayl)
                    for para in doc.paragraphs: final_content += para.text + "\n"
                elif ext in ['xls', 'xlsx']:
                    wb = openpyxl.load_workbook(fayl, data_only=True)
                    for row in wb.active.iter_rows(values_only=True):
                        final_content += " | ".join([str(c) for c in row if c]) + "\n"
            except Exception as e:
                return HttpResponse(f"Fayl tahlilida xatolik: {e}")

        if final_content.strip():
            # Xabarni bazaga saqlash
            ChatMessage.objects.create(
                user=user,
                text=f"🔴 DIQQAT! BAXTSIZ HODISA XABARI:\nYubordi: {user.full_name or user.login}\n{final_content}"
            )
        return redirect('/Baxtsizhodisalar/')

    # Ma'lumotlarni chiqarish
    messages = ChatMessage.objects.filter(text__contains="DIQQAT! BAXTSIZ HODISA").order_by('-created_at')
    messages_html = ""
    for m in messages:
        m_time = timezone.localtime(m.created_at).strftime('%H:%M | %d.%m.%Y')
        # Xabardan sarlavhani ajratib chiroyli ko'rsatish
        clean_text = m.text.replace("🔴 DIQQAT! BAXTSIZ HODISA XABARI:", "").strip()
        messages_html += f"""
            <div class="msg-card">
                <div class="msg-header"><i class="fas fa-bullhorn"></i> RASMIY BILDIRISHNOMA</div>
                <div class="msg-body">{clean_text}</div>
                <div class="msg-footer">{m_time}</div>
            </div>"""

    # Boss uchun xabar yuborish paneli
    boss_panel = ""
    if is_boss:
        boss_panel = f"""
                <div class="admin-box">
                    <h3 style="margin-top:0; color:#ff4b4b; font-size:16px;">BOSS: BILDIRISHNOMA YUBORISH</h3>
                    <form method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
                        <textarea name="text" placeholder="Voqea tafsilotlarini yozing..." required></textarea>
                        <div style="margin-top:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap: wrap; gap:10px;">
                            <label class="file-label">
                                <i class="fas fa-paperclip"></i> Fayl biriktirish
                                <input type="file" name="admin_file" accept=".pdf,.docx,.xlsx" style="display:none;">
                            </label>
                            <button type="submit" class="btn">YUBORISH</button>
                        </div>
                    </form>
                </div>"""

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Monitoring | TemirYo'l</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body {{ margin: 0; padding: 0; color: white; font-family: 'Segoe UI', sans-serif; overflow-x: hidden; background: #000; cursor: pointer; }}
                #bg-video {{ position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; z-index: -2; transform: translate(-50%, -50%); object-fit: cover; pointer-events: none; }}
                .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.75); z-index: -1; }}

                .header {{ background: rgba(60, 0, 0, 0.9); padding: 15px; text-align: center; border-bottom: 2px solid #ff4b4b; position: sticky; top: 0; z-index: 10; backdrop-filter: blur(15px); display: flex; align-items: center; justify-content: space-between; }}
                .header-title {{ flex-grow: 1; text-align: center; font-weight: 900; color: #ff4b4b; letter-spacing: 1px; }}

                .content {{ padding: 20px; max-width: 600px; margin: 0 auto; position: relative; z-index: 1; }}

                .admin-box {{ background: rgba(30, 0, 0, 0.5); padding: 20px; border-radius: 20px; margin-bottom: 30px; border: 1px solid rgba(255, 75, 75, 0.4); backdrop-filter: blur(10px); }}
                textarea {{ width: 100%; height: 100px; background: rgba(0,0,0,0.6); color: white; border-radius: 12px; padding: 12px; border: 1px solid #555; outline: none; resize: none; }}

                .file-label {{ background: rgba(255,255,255,0.1); padding: 10px 15px; border-radius: 10px; font-size: 13px; cursor: pointer; border: 1px dashed #777; }}

                .msg-card {{ background: rgba(40, 0, 0, 0.5); border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 15px; margin-bottom: 20px; backdrop-filter: blur(10px); animation: slideIn 0.4s ease-out; border-right: 1px solid rgba(255,255,255,0.05); }}
                @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(-20px); }} to {{ opacity: 1; transform: translateX(0); }} }}

                .msg-header {{ color: #ff4b4b; font-weight: bold; font-size: 12px; margin-bottom: 10px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }}
                .msg-body {{ white-space: pre-wrap; line-height: 1.6; font-size: 15px; color: #eee; }}
                .msg-footer {{ text-align: right; font-size: 10px; opacity: 0.5; margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); }}

                .btn {{ background: #ff4b4b; color: white; border: none; padding: 12px 30px; border-radius: 10px; cursor: pointer; font-weight: 900; transition: 0.3s; }}
                .btn:active {{ transform: scale(0.9); }}
            </style>
        </head>
        <body>
            <video loop playsinline id="bg-video">
                <source src="{video_url}" type="video/mp4">
            </video>
            <div class="overlay"></div>

            <div class="header">
                <a href="/second/" style="color:white; font-size: 20px;"><i class="fas fa-arrow-left"></i></a>
                <div class="header-title">Monitoring tizimi</div>
                <div style="width: 20px;"></div>
            </div>

            <div class="content">
                {boss_panel}
                {messages_html if messages_html else "<p style='text-align:center; opacity:0.5; margin-top:50px;'>Hozircha bildirishnomalar yo'q.</p>"}
            </div>

            <script>
                const video = document.getElementById('bg-video');

                function enableAudio() {{
                    video.muted = false;
                    video.volume = 0.8;
                    video.play().catch(e => console.log("Ovoz yoqilmadi"));
                }}

                // Foydalanuvchi sahifaning ixtiyoriy joyiga tegsa ovoz ishga tushadi
                document.body.addEventListener('click', enableAudio, {{ once: true }});
                document.body.addEventListener('touchstart', enableAudio, {{ once: true }});

                window.onload = () => {{
                    video.muted = true; // Dastlab jimjitlik
                    video.play();
                }};
            </script>
        </body>
        </html>
        """
    return HttpResponse(html)
def update_status(request):
    user_login = request.session.get('user_login')
    if user_login:
        UserProfile.objects.filter(login=user_login).update(last_seen=timezone.now())
        return HttpResponse("OK")
    return HttpResponse("Unauthorized", status=401)
def hisoblash_view(request):
    count_yakshanba = 0
    total_days = 0
    ish_kunlari = 0
    result_text = ""

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    user_okladi_str = request.GET.get('oklad')
    korsatkich_str = request.GET.get('korsatkich')

    video_url = static('uzb.mp4')

    if start_date_str and end_date_str and user_okladi_str and korsatkich_str:
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            user_okladi = float(user_okladi_str)
            korsatkich = float(korsatkich_str)

            if start > end:
                result_text = "<div style='background:rgba(255, 0, 0, 0.2); color:#ffcccc; padding:15px; border-radius:10px; text-align:center; margin-top:20px; border: 1px solid red;'>❌ Xato: Sana noto'g'ri kiritildi!</div>"
            else:
                current_date = start
                while current_date <= end:
                    total_days += 1
                    if current_date.weekday() == 6:  # Yakshanba
                        count_yakshanba += 1
                    current_date += timedelta(days=1)

                ish_kunlari = total_days - count_yakshanba
                foiz = 50 if korsatkich <= 20 else 75
                hisob_uchun_asos = user_okladi * (foiz / 100)
                KUNLIK_STAVKA = 100000
                ish_kunlari_uchun_haq = ish_kunlari * KUNLIK_STAVKA
                jami_summa = hisob_uchun_asos + ish_kunlari_uchun_haq

                result_text = f"""
                        <div style="margin-top: 25px; padding: 20px; border-radius: 15px; background: rgba(255,255,255,0.9); color: #333; box-shadow: 0 10px 20px rgba(0,0,0,0.4);">
                            <h3 style="color: #28a745; margin-top: 0; text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px;">📊 Hisobot Tafsiloti</h3>
                            <div style="font-size: 14px; line-height: 1.8;">
                                <p><b>1. Oklad bo'yicha:</b><br> {user_okladi:,.0f} × {foiz}% = <b>{hisob_uchun_asos:,.0f} so'm</b></p>
                                <p><b>2. Ish kunlari bo'yicha:</b><br> {ish_kunlari} kun × {KUNLIK_STAVKA:,.0f} = <b>{ish_kunlari_uchun_haq:,.0f} so'm</b></p>
                            </div>
                            <div style="text-align: center; background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px dashed #28a745;">
                                <span style="font-size: 13px; color: #666;">JAMI TO'LOV:</span><br>
                                <span style="color: #28a745; font-size: 26px; font-weight: 800;">{jami_summa:,.0f} so'm</span>
                            </div>
                        </div>
                    """
        except ValueError:
            result_text = "<div style='background:rgba(255, 0, 0, 0.2); color:#ffcccc; padding:15px; border-radius:10px; text-align:center; margin-top:20px; border: 1px solid red;'>⚠️ Ma'lumotlarni kiritishda xatolik!</div>"

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>To'lov Hisoblagich</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                body {{
                    margin: 0; padding: 0;
                    font-family: 'Segoe UI', Tahoma, sans-serif;
                    overflow: hidden;
                    height: 100vh;
                    display: flex; justify-content: center; align-items: center;
                    background: #000;
                }}

                #bg-video {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    min-width: 100%;
                    min-height: 100%;
                    width: auto;
                    height: auto;
                    z-index: -2;
                    transform: translate(-50%, -50%);
                    object-fit: cover;
                }}

                .overlay {{ 
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0, 0, 0, 0.6); z-index: -1; 
                }}

                .container {{
                    position: relative; z-index: 2; width: 90%; max-width: 420px;
                    background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
                    padding: 30px; border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.2);
                    color: white; box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                    max-height: 90vh; overflow-y: auto;
                }}

                h2 {{ text-align: center; margin-bottom: 25px; font-weight: 300; letter-spacing: 1px; color: #00f2ff; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ font-size: 11px; text-transform: uppercase; margin-bottom: 5px; display: block; color: #00f2ff; font-weight: bold; }}
                input {{
                    width: 100%; padding: 12px; border: 1px solid rgba(255,255,255,0.3); border-radius: 10px;
                    background: rgba(255,255,255,0.95); color: #000; font-size: 15px; box-sizing: border-box; outline: none;
                }}
                input:focus {{ border-color: #00f2ff; box-shadow: 0 0 10px rgba(0, 242, 255, 0.3); }}

                .btn-group {{ display: flex; gap: 10px; margin-top: 25px; }}
                .btn-calculate {{ 
                    flex: 2; padding: 14px; border: none; border-radius: 12px; 
                    background: #00f2ff; color: #000; font-weight: 900; 
                    cursor: pointer; transition: 0.3s; text-transform: uppercase;
                }}
                .btn-calculate:hover {{ background: #00d1dc; transform: translateY(-2px); }}

                .btn-back {{ 
                    flex: 1; padding: 14px; border: 1px solid rgba(255,255,255,0.4); 
                    border-radius: 12px; color: white; text-decoration: none; 
                    text-align: center; font-size: 13px; font-weight: bold;
                    display: flex; align-items: center; justify-content: center; transition: 0.3s;
                }}
                .btn-back:hover {{ background: rgba(255,255,255,0.1); }}
            </style>
        </head>
        <body>
            <video loop playsinline id="bg-video">
                <source src="{video_url}" type="video/mp4">
            </video>

            <div class="overlay"></div>

            <div class="container">
                <h2>💰 Hisoblagich</h2>
                <form method="GET">
                    <div class="form-group">
                        <label><i class="fas fa-calendar-alt"></i> Boshlanish:</label>
                        <input type="date" name="start_date" value="{start_date_str or ''}" required>
                    </div>
                    <div class="form-group">
                        <label><i class="fas fa-calendar-check"></i> Tugash:</label>
                        <input type="date" name="end_date" value="{end_date_str or ''}" required>
                    </div>
                    <div class="form-group">
                        <label><i class="fas fa-money-bill-wave"></i> Oklad (so'mda):</label>
                        <input type="number" name="oklad" value="{user_okladi_str or ''}" placeholder="Masalan: 4000000" required>
                    </div>
                    <div class="form-group">
                        <label><i class="fas fa-star"></i> Korsatkich (ball):</label>
                        <input type="number" name="korsatkich" value="{korsatkich_str or ''}" placeholder="Ballni kiriting" required>
                    </div>
                    <div class="btn-group">
                        <a href="/second/" class="btn-back">ORQAGA</a>
                        <button type="submit" class="btn-calculate">HISOBLASH</button>
                    </div>
                </form>
                {result_text}
            </div>

            <script>
                const video = document.getElementById('bg-video');

                // Sahifa yuklanishi bilan ovozni ochishga urinish
                window.addEventListener('DOMContentLoaded', () => {{
                    video.muted = false;
                    video.volume = 0.5;

                    let playPromise = video.play();

                    if (playPromise !== undefined) {{
                        playPromise.catch(error => {{
                            // Brauzer bloklasa muted holda boshlaymiz
                            video.muted = true;
                            video.play();
                        }});
                    }}
                }});

                // Foydalanuvchi birinchi marta ekranga tekkanda ovozni yoqish
                document.body.addEventListener('click', () => {{
                    if (video.muted) {{
                        video.muted = false;
                        video.volume = 0.5;
                        console.log("Ovoz yoqildi");
                    }}
                }}, {{ once: false }});
            </script>
        </body>
        </html>
        """
    return HttpResponse(html)
def get_safe_razryad(user):
    try:
        if not user or not user.razryad:
            return 0
        r_str = str(user.razryad).strip()
        if "/" in r_str:
            num, den = r_str.split("/")
            return float(num) / float(den)
        return float(r_str)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
def salary_menu_view(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    user = UserProfile.objects.filter(login=user_login).first()
    if not user:
        return redirect('/')

    # Razryadni tekshirish
    current_razryad = get_safe_razryad(user)

    if current_razryad >= (5 / 3):
        auto_url = "/Conculator/"
    else:
        auto_url = "/Kankulyator_Auto/"

    video_url = static('uzb.mp4')

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Oylik Menyusi | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ 
                margin: 0; padding: 0; height: 100vh; 
                font-family: 'Segoe UI', sans-serif; 
                display: flex; justify-content: center; align-items: center; 
                background: #000; color: white; overflow: hidden;
            }}

            /* VIDEO FON - TO'LIQ KO'RINISHI UCHUN */
            #bg-video {{
                position: fixed;
                top: 50%;
                left: 50%;
                min-width: 100%;
                min-height: 100%;
                width: auto;
                height: auto;
                z-index: -2;
                transform: translateX(-50%) translateY(-50%);
                object-fit: cover;
                background-size: cover;
            }}

            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.4); /* 0.7 dan 0.4 ga tushirildi - video aniqroq ko'rinadi */
                z-index: -1;
            }}

            .menu-box {{ 
                background: rgba(0, 0, 0, 0.6); /* Shaffof qora */
                padding: 40px 30px; 
                border-radius: 35px; 
                text-align: center; 
                width: 90%; max-width: 380px; 
                backdrop-filter: blur(10px); 
                border: 1px solid rgba(0, 242, 255, 0.3);
                box-shadow: 0 25px 50px rgba(0,0,0,0.8);
                position: relative; z-index: 1;
            }}

            h1 {{ 
                color: #fff; text-transform: uppercase; 
                font-size: 22px; margin-bottom: 10px; 
                letter-spacing: 2px; font-weight: 800;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }}

            .razryad-tag {{
                display: inline-block;
                padding: 6px 18px;
                background: rgba(0, 242, 255, 0.2);
                border: 1px solid #00f2ff;
                border-radius: 12px;
                color: #00f2ff;
                font-size: 14px;
                margin-bottom: 30px;
                font-weight: bold;
                text-shadow: 0 0 5px rgba(0,242,255,0.5);
            }}

            .nav-link {{ 
                display: flex; align-items: center; justify-content: center; gap: 10px;
                padding: 18px; margin: 15px 0; 
                background: #00f2ff; color: #000; 
                text-decoration: none; border-radius: 18px; 
                font-weight: 900; transition: 0.3s; 
                text-transform: uppercase;
                font-size: 14px;
            }}

            .nav-link:hover {{ 
                transform: translateY(-3px) scale(1.02); 
                box-shadow: 0 10px 20px rgba(0, 242, 255, 0.5); 
            }}

            .nav-manual {{ 
                background: transparent; 
                border: 2px solid #ff9d00; 
                color: #ff9d00; 
            }}

            .nav-manual:hover {{ 
                background: #ff9d00; 
                color: #000;
            }}

            .back-link {{ 
                color: rgba(255,255,255,0.7); 
                text-decoration: none; 
                font-size: 14px; 
                display: inline-block; 
                margin-top: 25px; 
                transition: 0.3s;
                font-weight: 500;
            }}
            .back-link:hover {{ color: #00f2ff; }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="menu-box">
            <i class="fas fa-calculator" style="font-size: 45px; color: #00f2ff; margin-bottom: 15px; filter: drop-shadow(0 0 10px #00f2ff);"></i>
            <h1>Oylik Hisoblash</h1>
            <div class="razryad-tag">Sizning razryadingiz: {user.razryad}</div>

            <a href="{auto_url}" class="nav-link">
                <i class="fas fa-robot"></i> Avtomatik hisob
            </a>

            <a href="/Kankulyator/" class="nav-link nav-manual">
                <i class="fas fa-edit"></i> Qo'lda kiritish
            </a>

            <a href="/second/" class="back-link"><i class="fas fa-arrow-left"></i> ORQAGA QAYTISH</a>
        </div>

        <script>
            const video = document.getElementById('bg-video');

            // Sahifa yuklanganda ovoz bilan o'ynatishga urinish
            window.addEventListener('load', () => {{
                video.muted = false;
                video.volume = 0.5;

                let playPromise = video.play();

                if (playPromise !== undefined) {{
                    playPromise.catch(error => {{
                        // Agar brauzer ovozli autoplayni bloklasa, muted qilib o'ynatamiz
                        video.muted = true;
                        video.play();
                        console.log("Ovoz bloklandi, muted holatda o'ynatilmoqda.");
                    }});
                }}
            }});

            // Sahifaning istalgan joyiga bosilganda ovozni majburiy yoqish
            document.body.addEventListener('click', () => {{
                if (video.muted) {{
                    video.muted = false;
                    video.play();
                    console.log("Ovoz foydalanuvchi orqali yoqildi.");
                }}
            }}, {{ once: false }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def common_calculator_logic(request, bonus_rate, check_type):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    user = UserProfile.objects.filter(login=user_login).first()

    salary = request.GET.get('salary')
    norma_soat = request.GET.get('norma_soat')
    ishlangan_soat = request.GET.get('ishlangan_soat')
    tungi_soat = request.GET.get('tungi_soat', '0')
    bayram_soati = request.GET.get('bayram_soati', '0')

    res_html = ""
    if salary and norma_soat and ishlangan_soat:
        try:
            s, n_s, i_s = float(salary), float(norma_soat), float(ishlangan_soat)
            t_s, b_s = float(tungi_soat or 0), float(bayram_soati or 0)

            m = s / n_s
            # Hisoblash formulasi
            brutto = (m * i_s) + (m * i_s * bonus_rate) + (t_s * m * 0.5) + ((490000 / n_s) * i_s) + (b_s * m)
            soliq = brutto * 0.131
            netto = brutto - soliq

            res_html = f"""
            <div style="background: rgba(0, 242, 255, 0.15); border: 1px solid #00f2ff; padding: 20px; border-radius: 20px; margin-top: 20px; text-align: center; backdrop-filter: blur(10px);">
                <span style="color:#ddd; font-size: 14px; text-transform: uppercase;">Qo'lga tegadigan summa:</span><br>
                <b style="color:#00f2ff; font-size: 26px; text-shadow: 0 0 10px rgba(0,242,255,0.5);">{netto:,.0f} so'm</b>
            </div>"""
        except:
            res_html = "<p style='color:#ff4b4b; text-align:center;'>⚠️ Ma'lumotlarni kiritishda xatolik!</p>"

    # Video manzili
    video_url = static('uzb.mp4')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kalkulyator | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background: #000; color: white; overflow-x: hidden; }}

            #bg-video {{
                position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%;
                width: auto; height: auto; z-index: -2; transform: translate(-50%, -50%);
                object-fit: cover;
            }}

            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.4); z-index: -1;
            }}

            .container {{
                max-width: 450px; margin: 40px auto; padding: 25px;
                background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(15px);
                border-radius: 30px; border: 1px solid rgba(0, 242, 255, 0.2);
                position: relative; z-index: 1; box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            }}

            h2 {{ text-align: center; color: #00f2ff; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 25px; }}

            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; font-size: 12px; color: #00f2ff; margin-bottom: 5px; font-weight: bold; text-transform: uppercase; }}

            input {{
                width: 100%; padding: 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.9); color: #000; font-size: 16px; font-weight: 600; outline: none; box-sizing: border-box;
            }}

            .btn-calc {{
                width: 100%; padding: 15px; border: none; border-radius: 15px;
                background: #00f2ff; color: #000; font-weight: 900; font-size: 16px;
                cursor: pointer; text-transform: uppercase; transition: 0.3s; margin-top: 10px;
            }}
            .btn-calc:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,242,255,0.4); }}

            .back-btn {{
                display: block; text-align: center; margin-top: 20px; color: rgba(255,255,255,0.6);
                text-decoration: none; font-size: 14px;
            }}
            .back-btn:hover {{ color: #fff; }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="container">
            <a href="/second/" class="back-btn" style="text-align: left; margin: 0 0 15px 0;">
                <i class="fas fa-arrow-left"></i> ORQAGA
            </a>
            <h2>Hisob-kitob</h2>
            <form method="GET">
                <div class="form-group">
                    <label>Oklad:</label>
                    <input type="number" name="salary" value="{salary or ''}" required placeholder="Masalan: 4000000">
                </div>
                <div class="form-group">
                    <label>Norma soat:</label>
                    <input type="number" name="norma_soat" value="{norma_soat or ''}" required>
                </div>
                <div class="form-group">
                    <label>Ishlangan soat:</label>
                    <input type="number" name="ishlangan_soat" value="{ishlangan_soat or ''}" required>
                </div>
                <div class="form-group">
                    <label>Tungi soat:</label>
                    <input type="number" name="tungi_soat" value="{tungi_soat or '0'}">
                </div>
                <div class="form-group">
                    <label>Bayram soati:</label>
                    <input type="number" name="bayram_soati" value="{bayram_soati or '0'}">
                </div>
                <button type="submit" class="btn-calc">HISOBLASH</button>
            </form>
            {res_html}
        </div>

        <script>
            const video = document.getElementById('bg-video');

            window.addEventListener('load', () => {{
                video.muted = false;
                video.volume = 0.5;
                let playPromise = video.play();
                if (playPromise !== undefined) {{
                    playPromise.catch(() => {{
                        video.muted = true;
                        video.play();
                    }});
                }}
            }});

            document.body.addEventListener('click', () => {{
                if (video.muted) {{
                    video.muted = false;
                    video.play();
                }}
            }}, {{ once: false }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)
def salary_calc_manual_view(request):
    user_login = request.session.get('user_login')
    if not user_login: return redirect('/')

    salary = request.GET.get('salary')
    norma_soat = request.GET.get('norma_soat')
    ishlangan_soat = request.GET.get('ishlangan_soat')
    bonus_percent = request.GET.get('bonus_percent')
    tungi_soat = request.GET.get('tungi_soat', '0')
    bayram_soati = request.GET.get('bayram_soati', '0')

    res_html = ""
    if salary and norma_soat and ishlangan_soat and bonus_percent:
        try:
            s, n, i = float(salary), float(norma_soat), float(ishlangan_soat)
            bp = float(bonus_percent) / 100
            ts, bs = float(tungi_soat or 0), float(bayram_soati or 0)

            m = s / n
            brutto = (m * i) + (m * i * bp) + (ts * m * 0.5) + ((490000 / n) * i) + (bs * m)
            netto = brutto - (brutto * 0.131)

            res_html = f"""
            <div style="background: rgba(255, 157, 0, 0.2); border: 1px solid #ff9d00; padding: 20px; border-radius: 20px; margin-top: 20px; text-align: center; backdrop-filter: blur(10px);">
                <span style="color:#eee; font-size: 14px; text-transform: uppercase;">Hisoblangan sof oylik:</span><br>
                <b style="color:#ff9d00; font-size: 26px; text-shadow: 0 0 10px rgba(255,157,0,0.5);">{netto:,.0f} so'm</b>
            </div>"""
        except:
            res_html = "<p style='color:#ff4b4b; text-align:center;'>⚠️ Ma'lumotlarda xatolik!</p>"

    video_url = static('uzb.mp4')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manual Kalkulyator | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background: #000; color: white; overflow-x: hidden; }}

            #bg-video {{
                position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%;
                width: auto; height: auto; z-index: -2; transform: translate(-50%, -50%);
                object-fit: cover;
            }}

            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.4); z-index: -1;
            }}

            .container {{
                max-width: 450px; margin: 30px auto; padding: 25px;
                background: rgba(0, 0, 0, 0.65); backdrop-filter: blur(15px);
                border-radius: 30px; border: 1px solid rgba(255, 157, 0, 0.3);
                position: relative; z-index: 1; box-shadow: 0 20px 50px rgba(0,0,0,0.7);
                max-height: 95vh; overflow-y: auto;
            }}

            h2 {{ text-align: center; color: #ff9d00; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 25px; font-weight: 800; }}

            .form-group {{ margin-bottom: 12px; }}
            label {{ display: block; font-size: 11px; color: #ff9d00; margin-bottom: 4px; font-weight: bold; text-transform: uppercase; }}

            input {{
                width: 100%; padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.95); color: #000; font-size: 15px; font-weight: 600; outline: none; box-sizing: border-box;
            }}
            input:focus {{ border-color: #ff9d00; box-shadow: 0 0 8px rgba(255,157,0,0.4); }}

            .btn-calc {{
                width: 100%; padding: 14px; border: none; border-radius: 15px;
                background: #ff9d00; color: #000; font-weight: 900; font-size: 16px;
                cursor: pointer; text-transform: uppercase; transition: 0.3s; margin-top: 15px;
            }}
            .btn-calc:hover {{ background: #e68a00; transform: translateY(-2px); }}

            .back-btn {{
                display: inline-block; color: #ff9d00; text-decoration: none; font-size: 14px; font-weight: bold; margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="container">
            <a href="/okladmenu/" class="back-btn"><i class="fas fa-arrow-left"></i> ORQAGA</a>
            <h2><i class="fas fa-edit"></i> Qo'lda kiritish</h2>
            <form method="GET">
                <div class="form-group">
                    <label>Oklad (tarif stavka):</label>
                    <input type="number" name="salary" value="{salary or ''}" required>
                </div>
                <div class="form-group">
                    <label>Norma soat:</label>
                    <input type="number" name="norma_soat" value="{norma_soat or ''}" required>
                </div>
                <div class="form-group">
                    <label>Ishlangan soat:</label>
                    <input type="number" name="ishlangan_soat" value="{ishlangan_soat or ''}" required>
                </div>
                <div class="form-group">
                    <label>Mukofot (foizda):</label>
                    <input type="number" name="bonus_percent" value="{bonus_percent or ''}" placeholder="Masalan: 20" required>
                </div>
                <div class="form-group">
                    <label>Tungi soat (1.5 baravar):</label>
                    <input type="number" name="tungi_soat" value="{tungi_soat or '0'}">
                </div>
                <div class="form-group">
                    <label>Bayram soati (2 baravar):</label>
                    <input type="number" name="bayram_soati" value="{bayram_soati or '0'}">
                </div>
                <button type="submit" class="btn-calc">HISOBLASH</button>
            </form>
            {res_html}
        </div>

        <script>
            const video = document.getElementById('bg-video');

            window.addEventListener('load', () => {{
                video.muted = false;
                video.volume = 0.5;
                let playPromise = video.play();
                if (playPromise !== undefined) {{
                    playPromise.catch(() => {{
                        video.muted = true;
                        video.play();
                        console.log("Ovoz kutish rejimida...");
                    }});
                }}
            }});

            // Birinchi bosishda ovozni majburiy yoqish
            document.body.addEventListener('click', () => {{
                if (video.muted) {{
                    video.muted = false;
                    video.play();
                }}
            }}, {{ once: false }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)
def render_page(rate, s, n, i, ts, bs, res_html, is_manual=False, bonus_percent=""):
    title = "QO'LDA KIRITISH" if is_manual else f"{int(rate * 100)}% KALKULYATOR"
    color = "#ff9d00" if is_manual else "#00f2ff"
    bonus_field = f'<label>Mukofot foizi (%):</label><input type="number" name="bonus_percent" value="{bonus_percent}" required>' if is_manual else ""

    return HttpResponse(f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; background: #000; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: #fff; }}
            .main-bg {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("/static/image.jpg") center/cover; z-index: -1; }}
            .box {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(25px); padding: 30px; border-radius: 30px; width: 90%; max-width: 380px; border: 1px solid rgba(255,255,255,0.1); }}
            h2 {{ color: {color}; text-align: center; font-size: 18px; }}
            input {{ width: 100%; padding: 12px; margin: 8px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: #fff; box-sizing: border-box; }}
            button {{ width: 100%; padding: 15px; border-radius: 20px; border: none; background: {color}; color: #000; font-weight: bold; cursor: pointer; margin-top: 15px; }}
            label {{ font-size: 11px; color: {color}; text-transform: uppercase; margin-left: 5px; }}
        </style>
    </head>
    <body>
        <div class="main-bg"></div>
        <div class="box">
            <h2>{title}</h2>
            {res_html}
            <form method="GET">
                <label>Oklad:</label><input type="number" name="salary" value="{s or ''}" required>
                <label>Norma soat:</label><input type="number" name="norma_soat" value="{n or ''}" required>
                <label>Ishlangan soat:</label><input type="number" name="ishlangan_soat" value="{i or ''}" required>
                {bonus_field}
                <label>Tungi soat:</label><input type="number" name="tungi_soat" value="{ts or 0}">
                <label>Bayram soati:</label><input type="number" name="bayram_soati" value="{bs or 0}">
                <button type="submit">HISOBLASH</button>
            </form>
            <a href="/second/" style="display:block; text-align:center; color:#666; margin-top:15px; text-decoration:none; font-size:13px;">← ORQAGA</a>
        </div>
    </body>
    </html>
    """)
def salary_calc_view(request):
    return common_calculator_logic(request, 0.20, "high")
def salary_calc_view1(request):
    return common_calculator_logic(request, 0.40, "low")
def boss(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/login/')

    user = UserProfile.objects.filter(login=user_login).first()
    # Faqat boss ekanligini tekshiramiz
    if not user or not user.is_boss:
        return redirect('/second/')  # Agar boss bo'lmasa oddiy menyuga qaytaradi

    video_url = static('uzb.mp4')
    avatar_url = user.image.url if hasattr(user, 'image') and user.image else static('default_avatar.png')
    display_name = user.full_name if user.full_name else user.login
    guruh_nomi = user.otryad.nomi if hasattr(user, 'otryad') and user.otryad else "Bo'lim tayinlanmagan"

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Boss Panel | {display_name}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {{
                --accent: #00f2ff;
                --boss-red: #ff4747;
                --glass: rgba(255, 255, 255, 0.1);
            }}
            body {{ margin: 0; background: #000; color: #fff; font-family: 'Poppins', sans-serif; overflow-x: hidden; }}
            #bg-video {{ position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; z-index: -2; transform: translate(-50%, -50%); object-fit: cover; filter: brightness(0.5); }}
            .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: -1; }}

            .header {{ position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); z-index: 1000; border-bottom: 1px solid var(--boss-red); }}

            .container {{ padding: 20px; max-width: 500px; margin: 0 auto; }}
            .menu-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}

            .card {{ 
                background: var(--glass); backdrop-filter: blur(10px); border-radius: 20px; 
                padding: 25px 10px; text-decoration: none; color: #fff; 
                border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; 
                display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center;
            }}
            .card:active {{ transform: scale(0.95); background: rgba(255,255,255,0.2); }}
            .card i {{ font-size: 32px; color: var(--accent); }}

            /* Boss Maxsus Tugmalari */
            .boss-main {{ grid-column: span 2; border: 2px solid var(--boss-red); background: rgba(255, 71, 71, 0.15); }}
            .boss-main i {{ color: var(--boss-red); text-shadow: 0 0 10px var(--boss-red); }}

            .pulse {{ animation: pulse-animation 2s infinite; }}
            @keyframes pulse-animation {{
                0% {{ box-shadow: 0 0 0 0px rgba(255, 71, 71, 0.5); }}
                100% {{ box-shadow: 0 0 0 15px rgba(255, 71, 71, 0); }}
            }}

            .logout {{ grid-column: span 2; border-color: #555; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <video autoplay loop playsinline id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        <div class="overlay"></div>

        <div class="header">
            <div style="font-weight:900; color:var(--boss-red);">BOSS PANEL</div>
            <div style="display:flex; align-items:center;">
                <span style="margin-right:10px; font-size:14px;">{display_name}</span>
                <img src="{avatar_url}" style="width:34px; height:34px; border-radius:50%; border:2px solid var(--boss-red); object-fit: cover;">
            </div>
        </div>

        <div class="container">
            <p style="text-align:center; color:var(--accent); font-size:14px; margin-bottom:20px;">Bo'lim: {guruh_nomi}</p>

            <div class="menu-grid">
                <a href="/worker-list/" class="card boss-main pulse">
                    <i class="fas fa-satellite-dish"></i>
                    <span>JONLI KUZATUV</span>
                </a>



                <a href="/profile/" class="card">
                    <i class="fas fa-user-circle"></i>
                    <span>PROFIL</span>
                </a>

                <a href="/Baxtsizhodisalar/" class="card">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>HODISALAR</span>
                </a>

                <a href="https://t.me/+HxJsZu-uZJA2NzBi" class="card">
                    <i class="fab fa-telegram"></i>
                    <span>KANAL</span>
                </a>

                <a href="https://t.me/+IizmDY0I_4BkYzQy" class="card">
                    <i class="fas fa-headset"></i>
                    <span>MUROJAAT</span>
                </a>

                <a href="/logout/" class="card logout">
                    <i class="fas fa-power-off" style="color: #ff4747;"></i>
                    <span>CHIQISH</span>
                </a>
            </div>
        </div>

        <script>
            // Video ovozi uchun interaksiya
            document.body.addEventListener('click', () => {{
                const v = document.getElementById('bg-video');
                v.muted = false; v.volume = 0.5;
            }}, {{ once: true }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def update_location(request):
    """ Ishchi sahifasida JS orqali har 30-60 soniyada nuqta yozib boradi """
    if request.method == 'POST':
        user_login = request.session.get('user_login')
        user = UserProfile.objects.filter(login=user_login).first()

        if user and user.is_working:
            lat = request.POST.get('lat')
            lng = request.POST.get('lng')

            if lat and lng:
                user.latitude = lat
                user.longitude = lng
                user.last_seen = timezone.now()
                user.save()

                # Har bir harakat nuqtasini tarixga saqlash
                LocationHistory.objects.create(
                    user=user,
                    latitude=float(lat),
                    longitude=float(lng)
                )
                return JsonResponse({'status': 'saved'})

    return JsonResponse({'status': 'ignored'})
def second_view(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/login/')

    user = UserProfile.objects.filter(login=user_login).first()
    if not user or not user.is_active:
        request.session.flush()
        return redirect('/login/')

    # Boss bo'lsa boshqaruv paneliga yuborish
    if getattr(user, 'is_boss', False):
        return redirect('/bosspage/')

    # 1. 24 SOATLIK AVTOMATIK TO'XTATISH (Xavfsizlik uchun)
    is_working = getattr(user, 'is_working', False)
    if is_working and user.work_start_time:
        diff = timezone.now() - user.work_start_time
        if diff.total_seconds() >= 86400:
            user.is_working = False
            user.save()
            is_working = False

    # Resurslar
    video_url = static('uzb.mp4')
    avatar_url = user.image.url if hasattr(user, 'image') and user.image else static('default_avatar.png')
    csrf_token = get_token(request)
    display_name = user.full_name if user.full_name else user.login

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Bosh Menyu</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {{
                --accent: #00f2ff;
                --green: #00ff88;
                --danger: #ff4747;
                --glass: rgba(255, 255, 255, 0.1);
            }}
            body {{ margin: 0; background: #000; color: #fff; font-family: 'Segoe UI', sans-serif; padding-bottom: 80px; overflow-x: hidden; }}

            #bg-video {{ position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; z-index: -2; transform: translate(-50%, -50%); object-fit: cover; filter: brightness(0.4); }}
            .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.3); z-index: -1; }}

            .header {{ position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); z-index: 1000; border-bottom: 1px solid rgba(255,255,255,0.1); }}
            .user-info {{ display: flex; align-items: center; gap: 10px; }}
            .user-info img {{ width: 35px; height: 35px; border-radius: 50%; border: 2px solid var(--accent); object-fit: cover; }}

            .container {{ padding: 20px; max-width: 500px; margin: 0 auto; }}
            .menu-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}

            .card {{ 
                background: var(--glass); backdrop-filter: blur(10px); border-radius: 20px; 
                padding: 25px 10px; text-decoration: none; color: #fff; 
                border: 1px solid rgba(255,255,255,0.15); transition: 0.3s; 
                display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; text-align: center;
                cursor: pointer;
            }}
            .card i {{ font-size: 28px; color: var(--accent); }}
            .card:active {{ transform: scale(0.95); }}

            .work-btn {{ grid-column: span 2; font-weight: 900; border: none; }}
            .btn-start {{ background: linear-gradient(45deg, var(--accent), var(--green)); color: #000; }}
            .btn-stop {{ background: var(--danger); color: #fff; animation: pulse 2s infinite; }}

            @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0px rgba(255, 71, 71, 0.5); }} 100% {{ box-shadow: 0 0 0 15px rgba(255, 71, 71, 0); }} }}

            .bottom-nav {{ 
                position: fixed; bottom: 0; left: 0; width: 100%; 
                background: rgba(0,0,0,0.9); backdrop-filter: blur(20px);
                display: flex; justify-content: space-around; padding: 12px 0;
                border-top: 1px solid rgba(255,255,255,0.1); z-index: 2000;
            }}
            .nav-item {{ color: #888; text-decoration: none; display: flex; flex-direction: column; align-items: center; gap: 5px; font-size: 11px; }}
            .nav-item.active {{ color: var(--accent); }}
        </style>
    </head>
    <body>
        <video autoplay loop playsinline muted id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        <div class="overlay"></div>

        <div class="header">
            <div style="font-weight:900; color:var(--accent); letter-spacing:1px;">TEMIRYO'L</div>
            <div class="user-info">
                <span>{display_name}</span>
                <img src="{avatar_url}">
            </div>
        </div>

        <div class="container">
            <div class="menu-grid">
                <div id="workToggle" class="card work-btn {'btn-stop' if is_working else 'btn-start'}" onclick="toggleWork()">
                    <i class="fas fa-power-off"></i>
                    <span id="workText">{'ISHNI TUGATISH' if is_working else 'ISHGA KELDIM'}</span>
                </div>

                <a href="/okladmenu/" class="card"><i class="fas fa-coins"></i><span>Oylik</span></a>
                <a href="/tatil/" class="card"><i class="fas fa-umbrella-beach"></i><span>Ta'til</span></a>
                <a href="/hisobot/" class="card"><i class="fas fa-chart-line"></i><span>Hisobot</span></a>
                <a href="/Baxtsizhodisalar/" class="card"><i class="fas fa-exclamation-triangle"></i><span>Hodisalar</span></a>
                <a href="/profile/" class="card"><i class="fas fa-sliders"></i><span>Sozlamalar</span></a>
                <a href="https://t.me/+" class="card"><i class="fab fa-telegram"></i><span>Kanal</span></a>
            </div>
        </div>

        <div class="bottom-nav">
            <a href="/second/" class="nav-item active"><i class="fas fa-home"></i><span>Asosiy</span></a>
            <a href="/chats/" class="nav-item"><i class="fas fa-comments"></i><span>Chatlar</span></a>
            <a href="/profile/" class="nav-item"><i class="fas fa-user"></i><span>Profil</span></a>
            <a href="/logout/" class="nav-item" style="color:var(--danger);"><i class="fas fa-sign-out-alt"></i><span>Chiqish</span></a>
        </div>

        <script>
            let isWorking = {'true' if is_working else 'false'};
            let watchId = null;

            // Agar ishchi "Ishda" bo'lsa, GPSni boshlaymiz
            if(isWorking) startGPS();

            async function toggleWork() {{
                const action = isWorking ? 'stop' : 'start';

                // Statusni o'zgartirish so'rovi
                const res = await fetch('/toggle-work/', {{
                    method: 'POST',
                    headers: {{ 'X-CSRFToken': '{csrf_token}' }},
                    body: new URLSearchParams({{ 'action': action }})
                }});

                if(res.ok) {{
                    location.reload();
                }}
            }}

            function startGPS() {{
                if(navigator.geolocation) {{
                    watchId = navigator.geolocation.watchPosition(pos => {{
                        sendLocation(pos.coords.latitude, pos.coords.longitude);
                    }}, err => console.error("GPS Error:", err), {{ 
                        enableHighAccuracy: true,
                        maximumAge: 0 
                    }});
                }}
            }}

            async function sendLocation(lat, lng) {{
                const data = new FormData();
                data.append('lat', lat);
                data.append('lng', lng);
                data.append('csrfmiddlewaretoken', '{csrf_token}');

                try {{
                    await fetch('/update-location/', {{ method: 'POST', body: data }});
                }} catch(e) {{
                    console.log("Tarmoq xatosi");
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def profile_view(request):
    # 1. Sessiya va Userni tekshirish
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    user = UserProfile.objects.filter(login=user_login).first()
    if not user:
        return redirect('/')

    # 2. Ma'lumotlarni yangilash (POST)
    if request.method == "POST":
        new_name = request.POST.get('display_name')
        new_pic = request.FILES.get('profile_pic')

        if new_name:
            user.login = new_name
        if new_pic:
            user.image = new_pic

        user.save()
        request.session['user_login'] = user.login
        return redirect('/profile/')

    # 3. O'zgaruvchilar
    avatar_url = user.image.url if hasattr(user, 'image') and user.image else static('default_avatar.png')
    video_url = static('uzb.mp4')
    token = get_token(request)
    user_razryad = getattr(user, 'razryad', 'Kiritilmagan')

    # 4. HTML Dizayn
    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Profil | {user.login}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body {{ 
                margin: 0; min-height: 100vh; display: flex; justify-content: center; 
                align-items: center; background: #000; font-family: 'Segoe UI', sans-serif; 
                color: white; padding: 20px; overflow: hidden;
            }}

            /* VIDEO FON - TO'LIQ VA ANIQ KO'RINISHI UCHUN */
            #bg-video {{
                position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%;
                z-index: -2; transform: translate(-50%, -50%); object-fit: cover;
            }}

            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.4); /* Video yaxshi ko'rinishi uchun xiralik kamaytirildi */
                z-index: -1;
            }}

            .profile-card {{
                background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(15px);
                padding: 30px; border-radius: 40px; width: 100%; max-width: 380px; text-align: center;
                border: 1px solid rgba(0, 242, 255, 0.3); box-shadow: 0 25px 50px rgba(0,0,0,0.8);
                position: relative; z-index: 1;
            }}

            .avatar-container {{ position: relative; width: 110px; height: 110px; margin: 0 auto 15px; }}
            .avatar {{ 
                width: 110px; height: 110px; border-radius: 50%; 
                object-fit: cover; border: 3px solid #00f2ff;
                box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);
            }}

            .upload-btn {{
                position: absolute; bottom: 0; right: 0; background: #00f2ff; color: #000;
                width: 30px; height: 30px; border-radius: 50%; display: flex; justify-content: center;
                align-items: center; cursor: pointer; font-size: 14px; border: 2px solid #000;
            }}

            h2 {{ color: #fff; margin: 10px 0 5px; letter-spacing: 1px; font-weight: 800; }}
            .razryad-badge {{ 
                background: rgba(0, 242, 255, 0.15); color: #00f2ff; padding: 5px 15px; 
                border-radius: 12px; font-size: 14px; font-weight: bold; margin-bottom: 10px; 
                display: inline-block; border: 1px solid rgba(0, 242, 255, 0.3); 
            }}
            .tabel-label {{ color: rgba(255,255,255,0.7); font-size: 13px; margin-bottom: 25px; display: block; }}

            .input-group {{ text-align: left; margin-bottom: 20px; }}
            label {{ font-size: 11px; color: #00f2ff; margin-left: 15px; text-transform: uppercase; font-weight: bold; }}
            input[type="text"] {{
                width: 100%; padding: 12px 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.2);
                background: rgba(255,255,255,0.9); color: #000; outline: none; box-sizing: border-box; 
                margin-top: 5px; font-weight: 600;
            }}

            .save-btn {{
                width: 100%; padding: 14px; border-radius: 20px; border: none;
                background: #00f2ff; color: #000; font-weight: 900; cursor: pointer; 
                transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px;
            }}
            .save-btn:hover {{ transform: scale(1.02); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4); }}

            .logout-btn {{
                display: flex; align-items: center; justify-content: center; gap: 8px;
                width: 100%; margin-top: 15px; padding: 12px; border-radius: 20px;
                background: rgba(255, 71, 71, 0.15); color: #ff4747;
                text-decoration: none; font-size: 14px; font-weight: bold;
                border: 1px solid rgba(255, 71, 71, 0.3); transition: 0.3s;
            }}
            .logout-btn:hover {{ background: #ff4747; color: #fff; }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="profile-card">
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">

                <div class="avatar-container">
                    <img src="{avatar_url}" class="avatar" id="preview">
                    <label for="file-upload" class="upload-btn"><i class="fas fa-camera"></i></label>
                    <input id="file-upload" name="profile_pic" type="file" style="display:none;" onchange="previewImage(this)">
                </div>

                <h2>{user.login}</h2>
                <div class="razryad-badge"><i class="fas fa-award"></i> Razryad: {user_razryad}</div>
                <span class="tabel-label">Tabel raqami: {user.tabel_raqami}</span>

                <div class="input-group">
                    <label>Ismni tahrirlash:</label>
                    <input type="text" name="display_name" value="{user.login}">
                </div>

                <button type="submit" class="save-btn">Saqlash</button>
            </form>

            <a href="/logout/" class="logout-btn"><i class="fas fa-sign-out-alt"></i> Chiqish</a>
            <a href="/second/" style="color: rgba(0,242,255,0.8); text-decoration:none; display:block; margin-top:15px; font-size:13px; font-weight:bold; text-transform:uppercase;">← ASOSIY SAHIFA</a>
        </div>

        <script>
            function previewImage(input) {{
                if (input.files && input.files[0]) {{
                    var reader = new FileReader();
                    reader.onload = function(e) {{
                        document.getElementById('preview').src = e.target.result;
                    }}
                    reader.readAsDataURL(input.files[0]);
                }}
            }}

            const video = document.getElementById('bg-video');

            // Sahifa yuklanganda ovoz bilan o'ynatish
            window.addEventListener('load', () => {{
                video.muted = false;
                video.volume = 0.5;
                let playPromise = video.play();
                if (playPromise !== undefined) {{
                    playPromise.catch(() => {{
                        video.muted = true;
                        video.play();
                    }});
                }}
            }});

            // Ekranga tekkanda ovozni yoqish
            document.body.addEventListener('click', () => {{
                if (video.muted) {{
                    video.muted = false;
                    video.play();
                }}
            }}, {{ once: false }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def chats(request):
    user_login = request.session.get('user_login')

    # 1. Login tekshiruvi
    if not user_login:
        return redirect('/')

    current_user = UserProfile.objects.filter(login=user_login).first()
    if not current_user:
        return redirect('/')

    # Foydalanuvchining guruhi
    user_guruh = current_user.guruh

    # Har kirganda foydalanuvchi faolligini yangilash
    current_user.last_seen = timezone.now()
    current_user.save(update_fields=['last_seen'])

    besh_daqiqa_oldin = timezone.now() - timezone.timedelta(minutes=5)
    is_online = current_user.last_seen > besh_daqiqa_oldin
    status_text = "online" if is_online else f"oxirgi marta: {timezone.localtime(current_user.last_seen).strftime('%H:%M')}"

    # 2. POST so'rovlarini qayta ishlash
    if request.method == "POST":
        current_user.last_seen = timezone.now()
        current_user.save(update_fields=['last_seen'])

        delete_id = request.POST.get('delete_id')
        if delete_id:
            # Faqat o'z guruhi ichidagi o'z xabarini o'chira oladi
            msg = ChatMessage.objects.filter(id=delete_id, user=current_user, guruh=user_guruh).first()
            if msg:
                msg.delete()
                return HttpResponse("OK")

        text = request.POST.get('text')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        voice = request.FILES.get('voice')

        if text or image or video or voice:
            ChatMessage.objects.create(
                user=current_user,
                guruh=user_guruh, # Xabar guruhga biriktiriladi
                text=text, image=image, video=video, voice=voice
            )
            return HttpResponse("OK")

    # 3. Xabarlarni yig'ish funksiyasi (Faqat shu guruh uchun)
    def render_messages_html():
        # FILTER: Faqat foydalanuvchining guruhiga tegishli xabarlar
        all_messages = ChatMessage.objects.filter(guruh=user_guruh).order_by('created_at')
        html_out = ""
        for m in all_messages:
            is_me = m.user.login == user_login
            wrapper_cls = "my-wrapper" if is_me else "other-wrapper"
            bubble_cls = "my-bubble" if is_me else "other-bubble"
            m_time = timezone.localtime(m.created_at).strftime('%H:%M')
            sender_name = "Siz" if is_me else m.user.full_name

            options = ""
            if is_me:
                options = f'''
                        <div class="msg-options" onclick="event.stopPropagation(); toggleMenu({m.id})">
                            <i class="fas fa-ellipsis-v"></i>
                            <div class="options-menu" id="menu-{m.id}">
                                <button onclick="deleteMsg({m.id})"><i class="fas fa-trash"></i> O'chirish</button>
                            </div>
                        </div>'''

            media = ""
            if m.image: media += f'<img src="{m.image.url}" class="msg-media">'
            if m.video: media += f'<video src="{m.video.url}" controls class="msg-media"></video>'
            if m.voice: media += f'<audio src="{m.voice.url}" controls style="max-width: 100%;"></audio>'

            user_img = m.user.image.url if m.user.image else "/static/default_avatar.png"

            html_out += f'''
                    <div class="message-wrapper {wrapper_cls}" id="msg-{m.id}">
                        <img src="{user_img}" class="user-avatar" title="{sender_name}">
                        <div class="msg-bubble {bubble_cls}">
                            <div style="font-size: 11px; color: #00f2ff; font-weight: bold; margin-bottom: 3px;">{sender_name}</div>
                            {media}
                            <div class="msg-text">{m.text if m.text else ''}</div>
                            <span class="msg-time">{m_time}</span>
                        </div>
                        {options}
                    </div>'''
        return html_out

    if request.GET.get('update'):
        return HttpResponse(render_messages_html())

    csrf_token_value = get_token(request)
    video_url = static('uzb.mp4')
    initial_messages = render_messages_html()
    header_title = f"{user_guruh.nomi} Guruhi" if user_guruh else "Chat"

    html_template = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>{header_title}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                * {{ box-sizing: border-box; }}
                body {{
                    margin: 0; height: 100vh; display: flex; flex-direction: column;
                    background: #000;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    overflow: hidden;
                }}
                #bg-video {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    min-width: 100%;
                    min-height: 100%;
                    width: auto;
                    height: auto;
                    z-index: -2;
                    transform: translate(-50%, -50%); /* Videoni markazga tortadi */
                    object-fit: cover; /* Video nisbatini buzmagan holda ekranni to'ldiradi */
                }}
                .overlay {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0, 0, 0, 0.7); z-index: -1;
                }}
                .chat-header {{
                    background: rgba(20, 20, 20, 0.9); padding: 10px 15px;
                    display: flex; align-items: center; justify-content: space-between;
                    color: white; border-bottom: 1px solid rgba(0, 242, 255, 0.3); z-index: 10;
                    backdrop-filter: blur(10px);
                }}
                .chat-messages {{
                    flex: 1; overflow-y: auto; padding: 15px;
                    display: flex; flex-direction: column; gap: 10px;
                    scroll-behavior: smooth; position: relative; z-index: 1;
                }}
                .message-wrapper {{ display: flex; align-items: flex-end; gap: 8px; max-width: 85%; position: relative; }}
                .my-wrapper {{ align-self: flex-end; flex-direction: row-reverse; }}
                .user-avatar {{ width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid #00f2ff; }}
                .msg-bubble {{ padding: 8px 12px; border-radius: 14px; color: white; position: relative; line-height: 1.4; backdrop-filter: blur(5px); }}
                .my-bubble {{ background: rgba(0, 100, 150, 0.7); border-bottom-right-radius: 2px; border: 1px solid rgba(0, 242, 255, 0.2); }}
                .other-bubble {{ background: rgba(30, 30, 30, 0.8); border-bottom-left-radius: 2px; border: 1px solid rgba(255, 255, 255, 0.1); }}
                .msg-text {{ font-size: 15px; word-break: break-word; }}
                .msg-time {{ font-size: 10px; opacity: 0.5; float: right; margin-top: 4px; margin-left: 8px; }}
                .input-area {{
                    background: rgba(20, 20, 20, 0.95); padding: 10px 15px;
                    display: flex; align-items: center; gap: 12px; border-top: 1px solid rgba(0, 242, 255, 0.3);
                    backdrop-filter: blur(10px); z-index: 10;
                }}
                .input-wrapper {{ flex: 1; background: rgba(50, 50, 50, 0.8); border-radius: 22px; padding: 0 15px; border: 1px solid #444; }}
                .message-input {{ width: 100%; background: transparent; border: none; color: white; padding: 10px 0; outline: none; font-size: 16px; }}
                .icon-btn {{ color: #00f2ff; font-size: 20px; cursor: pointer; }}
                .send-btn {{ background: none; border: none; color: #00f2ff; font-size: 22px; cursor: pointer; }}
                .msg-media {{ max-width: 100%; border-radius: 10px; margin-bottom: 4px; }}
                .options-menu {{ 
                    display: none; position: absolute; background: #222; 
                    border-radius: 8px; right: 0; bottom: 35px; width: 130px; z-index: 100; 
                    box-shadow: 0 4px 12px rgba(0,242,255,0.2); border: 1px solid #444;
                }}
                .options-menu button {{ width: 100%; background: none; border: none; color: #ff4b4b; padding: 10px; text-align: left; cursor: pointer; }}
            </style>
        </head>
        <body>
            <video autoplay muted loop playsinline id="bg-video">
                <source src="{video_url}" type="video/mp4">
            </video>
            <div class="overlay"></div>

            <div class="chat-header">
                <a href="/second/" style="color:#00f2ff;"><i class="fas fa-arrow-left"></i></a>
                <div style="text-align:center;">
                    <h3 style="margin:0; font-size: 16px; color: #00f2ff;">{header_title}</h3>
                    <span style="font-size:11px; color:#aaa;">{status_text}</span>
                </div>
                <div style="width:20px;"></div>
            </div>

            <div class="chat-messages" id="chatContainer">{initial_messages}</div>

            <div class="input-area">
                <input type="file" id="fileInp" style="display:none" onchange="upFile()">
                <i class="fas fa-paperclip icon-btn" onclick="document.getElementById('fileInp').click()"></i>
                <div class="input-wrapper">
                    <input type="text" id="msgInp" class="message-input" placeholder="Xabar yozing..." autocomplete="off">
                </div>
                <button class="send-btn" onclick="hSend()"><i class="fas fa-paper-plane"></i></button>
            </div>

            <script>
                const chat = document.getElementById('chatContainer');
                chat.scrollTop = chat.scrollHeight;

                async function updateChat() {{
                    try {{
                        const res = await fetch('?update=1');
                        if (res.redirected) {{ window.location.href = "/"; return; }}
                        const html = await res.text();
                        const isAtBottom = chat.scrollTop + chat.clientHeight >= chat.scrollHeight - 100;
                        chat.innerHTML = html;
                        if (isAtBottom) chat.scrollTop = chat.scrollHeight;
                    }} catch (e) {{}}
                }}
                setInterval(updateChat, 3000);

                async function hSend() {{
                    const inp = document.getElementById('msgInp');
                    if(!inp.value.trim()) return;
                    const fd = new FormData();
                    fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                    fd.append('text', inp.value);
                    inp.value = '';
                    await fetch('', {{method:'POST', body:fd}});
                    updateChat();
                }}

                async function upFile() {{
                    const f = document.getElementById('fileInp').files[0];
                    if(!f) return;
                    const fd = new FormData();
                    fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                    if(f.type.startsWith('image')) fd.append('image', f);
                    else if(f.type.startsWith('video')) fd.append('video', f);
                    await fetch('', {{method:'POST', body:fd}});
                    updateChat();
                }}

                async function deleteMsg(id) {{
                    const fd = new FormData();
                    fd.append('delete_id', id);
                    fd.append('csrfmiddlewaretoken', '{csrf_token_value}');
                    await fetch('', {{method:'POST', body:fd}});
                    updateChat();
                }}

                function toggleMenu(id) {{
                    document.querySelectorAll('.options-menu').forEach(m => m.style.display = 'none');
                    const m = document.getElementById('menu-'+id);
                    if(m) m.style.display = 'block';
                }}
                window.onclick = () => document.querySelectorAll('.options-menu').forEach(m => m.style.display='none');
            </script>
        </body>
        </html>
        """
    return HttpResponse(html_template)
def logout_view(request):
    request.session.flush()
    return redirect('../') # Login sahifasiga qaytarish
def delete_message(request, msg_id):
    if request.method == "POST":
        msg = ChatMessage.objects.filter(id=msg_id).first()
        # Faqat o'z xabarini yoki admin o'chira olishi uchun:
        user_login = request.session.get('user_login')
        if msg and msg.user.login == user_login:
            msg.delete()
            return HttpResponse("OK")
    return HttpResponse("Xato", status=400)
def login(request):
    error_message = ""
    video_url = static('uzb.mp4')

    if request.method == "POST":
        u = request.POST.get('u_name', '').strip()
        p = request.POST.get('p_val', '').strip()

        if u == "1" and p == "1":
            return redirect('/boss-registration/')

        user = UserProfile.objects.filter(login__iexact=u).first()

        if not user:
            error_message = f'<div class="error-box"><i class="fas fa-user-times"></i> "{u}" logini topilmadi!</div>'
        elif user.password != p:
            error_message = '<div class="error-box"><i class="fas fa-lock"></i> Parol noto\'g\'ri!</div>'
        else:
            request.session['user_login'] = user.login
            return redirect('/second/')

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kirish | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {{ --yt: #ff0000; --neon: #00f2ff; }}
            * {{ box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
            body {{ margin: 0; height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #000; overflow: hidden; cursor: pointer; }}

            /* Video butun ekranni qoplaydi va uni bosib bo'lmaydi (pointer-events: none) */
            #bg-video {{ 
                position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; 
                z-index: -2; transform: translate(-50%, -50%); object-fit: cover;
                pointer-events: none; 
            }}
            .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.45); z-index: -1; }}

            .login-card {{
                background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(15px);
                padding: 40px 30px; border-radius: 32px; width: 90%; max-width: 400px;
                border: 1px solid rgba(0, 242, 255, 0.3); text-align: center;
                box-shadow: 0 20px 50px rgba(0,0,0,0.8); position: relative; z-index: 1;
            }}

            .brand-name {{ font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 30px; text-shadow: 0 0 10px var(--neon); }}
            input {{ width: 100%; padding: 16px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.9); color: #000; margin-bottom: 15px; outline: none; font-size: 16px; font-weight: 600; }}
            .login-btn {{ width: 100%; padding: 16px; border-radius: 14px; border: none; background: var(--neon); color: #000; font-weight: 900; cursor: pointer; text-transform: uppercase; transition: 0.3s; margin-top: 10px; }}
            .login-btn:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 5px 20px rgba(0, 242, 255, 0.5); }}
            .error-box {{ background: rgba(255, 71, 71, 0.2); color: #ff4747; padding: 14px; border-radius: 14px; margin-bottom: 20px; font-size: 13px; border: 1px solid rgba(255, 71, 71, 0.4); display: flex; align-items: center; justify-content: center; gap: 10px; font-weight: bold; }}

            #yt-modal {{
                position: fixed; inset: 0; background: rgba(0,0,0,0.98);
                z-index: 9999; display: flex; align-items: center; justify-content: center;
            }}
            .modal-content {{
                background: #000; padding: 45px 25px; border-radius: 40px;
                border: 2px solid var(--yt); text-align: center; width: 85%; max-width: 320px;
            }}
            .yt-icon {{ font-size: 70px; color: var(--yt); margin-bottom: 20px; }}
            .sub-btn {{
                display: block; background: var(--yt); color: white; padding: 16px;
                border-radius: 20px; text-decoration: none; font-weight: bold;
                margin: 25px 0 15px; font-size: 15px;
            }}
            .check-btn {{ background: transparent; border: 1px solid #444; color: #888; width: 100%; padding: 14px; border-radius: 20px; cursor: pointer; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div id="yt-modal">
            <div class="modal-content">
                <div class="yt-icon"><i class="fab fa-youtube"></i></div>
                <h2 style="margin:0; color:white;">TO'XTANG!</h2>
                <p style="color:#bbb; font-size:14px; margin-top:10px;">Tizimga kirish uchun YouTube kanalga obuna bo'lishingiz majburiy.</p>
                <a href="https://www.youtube.com/@gamerjaan-x6" target="_blank" class="sub-btn" onclick="didClickSub()">
                    <i class="fas fa-bell"></i> HOZIROQ OBUNA BO'LISH
                </a>
                <button class="check-btn" onclick="verifySub()">OBUNANI TEKSHIRISH</button>
                <p id="error-msg" style="color:#ff4444; font-size:11px; margin-top:12px; display:none; font-weight:bold;">AVVAL OBUNA BO'LISH TUGMASINI BOSING!</p>
            </div>
        </div>

        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="login-card">
            <div class="brand-name">Temir Yo'l</div>
            {error_message}
            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
                <input type="text" name="u_name" placeholder="Login" required>
                <input type="password" name="p_val" placeholder="Parol" required>
                <button type="submit" class="login-btn">Tizimga kirish</button>
            </form>
            <div style="margin-top: 25px;">
                <a href="/signup/" style="color: var(--neon); text-decoration: none; font-size: 14px; font-weight: bold; text-transform: uppercase;">Ro'yxatdan o'tish</a>
            </div>
        </div>

        <script>
            let clickedSub = false;
            const video = document.getElementById('bg-video');

            function didClickSub() {{ 
                clickedSub = true; 
            }}

            function verifySub() {{
                if(clickedSub) {{
                    document.getElementById('yt-modal').style.display = 'none';
                    localStorage.setItem('subscribed', 'true');
                    // Tugmani bosganda ovozni yoqish
                    playWithSound();
                }} else {{
                    document.getElementById('error-msg').style.display = 'block';
                }}
            }}

            function playWithSound() {{
                video.muted = false;
                video.volume = 1.0; // Maksimal ovoz
                video.play().catch(e => console.log("Ovoz bloklandi"));
            }}

            // Sahifaning istalgan joyiga birinchi tegish (click yoki touch)
            document.body.addEventListener('click', function() {{
                playWithSound();
            }}, {{ once: true }}); // Faqat bir marta ishlaydi

            window.onload = () => {{
                if(localStorage.getItem('subscribed') === 'true') {{
                    document.getElementById('yt-modal').style.display = 'none';
                }}
                // Dastlab ovozsiz fonda aylanaveradi
                video.muted = true;
                video.play();
            }};
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def track_worker(request, worker_id):
    # Tanlangan ishchini bazadan qidiramiz
    worker = UserProfile.objects.filter(id=worker_id).first()

    if not worker:
        return HttpResponse("<h2>Xato: Ishchi topilmadi!</h2><a href='/worker-list/'>Ro'yxatga qaytish</a>")

    # Xarita sahifasi (HTML + JS)
    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{worker.full_name or worker.login} | Kuzatuv</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            body {{ margin: 0; padding: 0; font-family: sans-serif; }}
            #map {{ height: 100vh; width: 100%; }}
            .nav-box {{ 
                position: fixed; top: 15px; left: 15px; z-index: 1000; 
                background: rgba(0,0,0,0.85); padding: 15px; border-radius: 12px; 
                color: white; border: 1px solid #00f2ff; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .back-link {{ color: #ff4747; text-decoration: none; font-weight: bold; display: block; margin-bottom: 5px; }}
            .worker-name {{ color: #00f2ff; font-size: 18px; display: block; }}
        </style>
    </head>
    <body>
        <div class="nav-box">
            <a href="/worker-list/" class="back-link">← Ro'yxatga qaytish</a>
            <span class="worker-name">{worker.full_name or worker.login}</span>
            <small id="status" style="color:#00ff88;">Kuzatilmoqda...</small>
        </div>

        <div id="map"></div>

        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script>
            // Boshlang'ich koordinatalar (agar bo'lmasa Toshkent markazi)
            let initialLat = {worker.latitude or 41.2995};
            let initialLng = {worker.longitude or 69.2401};

            var map = L.map('map').setView([initialLat, initialLng], 16);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            var marker = L.marker([initialLat, initialLng]).addTo(map)
                .bindPopup('{worker.full_name or worker.login} shu yerda')
                .openPopup();

            function updateLocation() {{
                fetch('/get-single-location/{worker.id}/')
                    .then(response => response.json())
                    .then(data => {{
                        if(data.lat && data.lng) {{
                            let newPos = [data.lat, data.lng];
                            marker.setLatLng(newPos);
                            map.panTo(newPos); // Xaritani ishchi bilan birga surish
                            document.getElementById('status').innerText = "Yangilandi: " + new Date().toLocaleTimeString();
                        }}
                    }})
                    .catch(err => {{
                        console.error("Xatolik:", err);
                        document.getElementById('status').innerText = "Aloqa uzildi...";
                        document.getElementById('status').style.color = "red";
                    }});
            }}

            // Har 5 soniyada yangilab turish
            setInterval(updateLocation, 5000);
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def worker_list(request):
    # Faqat hozir ishlayotgan (is_working=True) ishchilarni olamiz
    workers = UserProfile.objects.filter(is_working=True)
    video_url = static('uzb.mp4')  # Video manzili

    # Ro'yxatni shakllantirish
    workers_html = ""
    for w in workers:
        w_time = w.work_start_time.strftime('%H:%M') if w.work_start_time else "Yaqinda"
        workers_html += f"""
        <div class="worker-card">
            <div class="info">
                <span class="name">{w.full_name or w.login}</span>
                <span class="time"><i class="fas fa-clock"></i> {w_time} da boshlagan</span>
            </div>
            <a href="/track-worker/{w.id}/" class="track-btn">Kuzatish</a>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jonli Kuzatuv | Boss</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root {{ --accent: #00f2ff; --green: #00ff88; }}
            body {{ background: #000; color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; overflow-x: hidden; }}

            /* Video Background */
            #bg-video {{ position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%; z-index: -2; transform: translate(-50%, -50%); object-fit: cover; filter: brightness(0.4); }}
            .overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); z-index: -1; }}

            .header-nav {{ display: flex; align-items: center; margin-bottom: 25px; }}
            .back-btn {{ color: #fff; text-decoration: none; font-size: 20px; margin-right: 15px; }}
            .header-title {{ color: var(--accent); margin: 0; font-weight: 900; letter-spacing: 1px; font-size: 20px; }}

            .container {{ max-width: 500px; margin: 0 auto; }}

            .worker-card {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
                padding: 18px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                transition: 0.3s;
            }}
            .worker-card:active {{ transform: scale(0.98); }}

            .info {{ display: flex; flex-direction: column; gap: 5px; }}
            .name {{ font-weight: 900; font-size: 16px; color: #fff; }}
            .time {{ font-size: 12px; color: var(--green); display: flex; align-items: center; gap: 5px; }}

            .track-btn {{
                background: var(--accent);
                color: #000;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 12px;
                font-weight: 900;
                font-size: 13px;
                text-transform: uppercase;
                box-shadow: 0 4px 15px rgba(0, 242, 255, 0.3);
            }}

            .empty-state {{ text-align: center; margin-top: 50px; color: #666; font-style: italic; }}

            /* Radar animatsiyasi */
            .radar {{ width: 10px; height: 10px; background: var(--green); border-radius: 50%; display: inline-block; position: relative; margin-right: 5px; }}
            .radar::after {{ content: ''; position: absolute; width: 100%; height: 100%; background: var(--green); border-radius: 50%; animation: pulse 1.5s infinite; }}
            @keyframes pulse {{ 0% {{ transform: scale(1); opacity: 1; }} 100% {{ transform: scale(3); opacity: 0; }} }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="container">
            <div class="header-nav">
                <a href="/bosspage/" class="back-btn"><i class="fas fa-arrow-left"></i></a>
                <h2 class="header-title">JONLI KUZATUV</h2>
            </div>

            <div id="worker-container">
                {workers_html if workers_html else '<p class="empty-state">Hozirda hech kim ish joyida emas...</p>'}
            </div>
        </div>

        <script>
            const video = document.getElementById('bg-video');

            function startContent() {{
                video.muted = false;
                video.volume = 0.5;
                video.play().catch(err => console.log("Ovoz bloklandi"));
            }}

            // Sahifaga birinchi marta tegilganda ovozni yoqish
            document.body.addEventListener('click', startContent, {{ once: true }});
            document.body.addEventListener('touchstart', startContent, {{ once: true }});

            window.onload = () => {{
                video.muted = true;
                video.play();
            }};
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def map_view(request):
    user_id = request.GET.get('user_id')
    worker = UserProfile.objects.filter(id=user_id).first()

    if not worker: return HttpResponse("Ishchi topilmadi")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kuzatuv: {worker.full_name}</title>
        <meta http-equiv="refresh" content="15"> <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{ height: 100vh; width: 100%; }}</style>
    </head>
    <body style="margin:0;">
        <div style="position:fixed; top:10px; left:50px; z-index:1000; background:white; padding:10px; border-radius:5px;">
            <b>{worker.full_name}</b> (Jonli)<br>
            <small>Lat: {worker.latitude}, Lng: {worker.longitude}</small>
        </div>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{worker.latitude or 41.3}, {worker.longitude or 69.2}], 16);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
            L.marker([{worker.latitude or 0}, {worker.longitude or 0}]).addTo(map)
                .bindPopup("{worker.full_name} hozir shu yerda").openPopup();
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def boss_registration(request):
    # Otryad va Guruhlarni bazadan olish
    otryadlar = Otryad.objects.all()
    guruhlar = IshchiGuruh.objects.all()

    if request.method == "POST":
        # Formadan ma'lumotlarni olish
        f_name = request.POST.get('f_name', '').strip()
        l_name = request.POST.get('l_name', '').strip()
        u_login = request.POST.get('u_login')
        u_pass = request.POST.get('u_pass')
        u_phone = request.POST.get('phone')
        u_otryad_id = request.POST.get('otryad')
        u_guruh_id = request.POST.get('guruh')

        # Manzil ma'lumotlari
        viloyat = request.POST.get('viloyat')
        tuman = request.POST.get('tuman')
        mahalla = request.POST.get('mahalla')
        kocha = request.POST.get('kocha')
        uy = request.POST.get('uy')

        # Bazaga saqlash
        # DIQQAT: Modelingizda first_name/last_name yo'q, shuning uchun full_name ga birlashtiramiz
        new_boss = UserProfile.objects.create(
            full_name=f"{f_name} {l_name}",
            login=u_login,
            password=u_pass,
            phone=u_phone,
            tabel_raqami="BOSHLIQ",  # Modelda bu maydon majburiy bo'lgani uchun qiymat berdik
            otryad_id=u_otryad_id if u_otryad_id else None,
            guruh_id=u_guruh_id if u_guruh_id else None,
            viloyat=viloyat,
            shahar_tuman=tuman,
            mahalla=mahalla,
            kocha=kocha,
            uy_raqami=uy,
            is_boss=True,
            is_active=True  # Boshliq darrov tizimga kira olishi uchun
        )
        return redirect('/')

    # Registratsiya Formasi (Boshliqlar uchun) HTML qismi
    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Boshliqlar Registratsiyasi</title>
        <style>
            :root {{ --neon: #00f2ff; }}
            body {{ background: #050505; color: white; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; padding: 20px; }}
            .reg-box {{ background: #111; padding: 30px; border-radius: 25px; width: 100%; max-width: 450px; border: 1px solid var(--neon); box-shadow: 0 0 15px rgba(0, 242, 255, 0.2); }}
            h2 {{ color: var(--neon); text-align: center; text-transform: uppercase; letter-spacing: 2px; }}
            input, select {{ width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; border: 1px solid #333; background: #222; color: white; box-sizing: border-box; }}
            input:focus, select:focus {{ outline: none; border-color: var(--neon); }}
            .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            button {{ width: 100%; padding: 15px; background: var(--neon); border: none; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 20px; color: black; transition: 0.3s; }}
            button:hover {{ background: #00c8d4; transform: translateY(-2px); }}
            label {{ font-size: 12px; color: #888; margin-left: 5px; }}
        </style>
    </head>
    <body>
        <div class="reg-box">
            <h2>Boshliq Ro'yxati</h2>
            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">

                <div class="grid-2">
                    <input type="text" name="f_name" placeholder="Ism" required>
                    <input type="text" name="l_name" placeholder="Familiya" required>
                </div>

                <input type="text" name="u_login" placeholder="Login" required>
                <input type="password" name="u_pass" placeholder="Parol" required>
                <input type="text" name="phone" placeholder="Telefon (998...)" required>

                <label>Otryadni tanlang:</label>
                <select name="otryad">
                    <option value="">Tanlanmagan</option>
                    {"".join([f'<option value="{o.id}">{o.nomi}</option>' for o in otryadlar])}
                </select>

                <label>Guruhni tanlang:</label>
                <select name="guruh">
                    <option value="">Tanlanmagan</option>
                    {"".join([f'<option value="{g.id}">{g.nomi}</option>' for g in guruhlar])}
                </select>

                <hr style="border: 0.5px solid #222; margin: 15px 0;">
                <p style="font-size: 14px; color: var(--neon);">Yashash manzili:</p>

                <div class="grid-2">
                    <input type="text" name="viloyat" placeholder="Viloyat">
                    <input type="text" name="tuman" placeholder="Tuman">
                </div>
                <input type="text" name="mahalla" placeholder="Mahalla">
                <div class="grid-2">
                    <input type="text" name="kocha" placeholder="Ko'cha">
                    <input type="text" name="uy" placeholder="Uy raqami">
                </div>

                <button type="submit">TASDIQLASH VA SAQLASH</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
def signup(request):
    video_url = static('uzb.mp4')

    # Ma'lumotlarni bazadan olish
    otryadlar = Otryad.objects.all()
    guruhlar = IshchiGuruh.objects.all()

    # JavaScript uchun guruhlarni tayyorlash
    guruhlar_dict = {}
    for g in guruhlar:
        if g.otryad_id not in guruhlar_dict:
            guruhlar_dict[g.otryad_id] = []
        guruhlar_dict[g.otryad_id].append({'id': g.id, 'nomi': g.nomi})

    # JSON ga o'tkazish (f-string muammosini oldini olish uchun)
    guruhlar_json = json.dumps(guruhlar_dict)

    if request.method == "POST":
        u = request.POST.get('u_name')
        p = request.POST.get('p_val')
        tel = request.POST.get('tel_val')
        tabel = request.POST.get('t_raqam')
        fname = request.POST.get('full_name')
        raz_val = request.POST.get('razryad')
        guruh_id = request.POST.get('guruh_id')

        tariflar = {"5/3": 5336929, "5/2": 4800000, "4/3": 4100000}
        oklad_val = tariflar.get(raz_val, 0)

        if UserProfile.objects.filter(login=u).exists():
            return HttpResponse(
                "<h3 style='color:red; text-align:center; background:#000; height:100vh; display:flex; align-items:center; justify-content:center; margin:0;'>❌ Bu login band!</h3>")

        if u and p and tel and guruh_id:
            try:
                yangi_user = UserProfile(
                    login=u, password=p, phone=tel,
                    tabel_raqami=tabel, full_name=fname,
                    razryad=raz_val, oklad=oklad_val,
                    is_active=False, guruh_id=int(guruh_id)
                )
                yangi_user.save()
                return redirect(f'/verify-code/?login={u}')
            except Exception as e:
                return HttpResponse(f"<h3 style='color:orange;'>Xatolik: {e}</h3>")

    otryad_options = "".join([f'<option value="{o.id}">{o.nomi}</option>' for o in otryadlar])

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ro'yxatdan o'tish | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ 
                margin: 0; padding: 0; background-color: #000;
                min-height: 100vh; display: flex; justify-content: center; align-items: center;
                font-family: 'Segoe UI', Tahoma, sans-serif; overflow-x: hidden;
            }}
            #bg-video {{
                position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%;
                z-index: -2; transform: translate(-50%, -50%); object-fit: cover;
            }}
            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.45); z-index: -1;
            }}
            .container {{ 
                position: relative; z-index: 2; background: rgba(0, 0, 0, 0.65); 
                padding: 30px; border-radius: 35px; width: 95%; max-width: 420px; 
                border: 1px solid rgba(0, 242, 255, 0.3); backdrop-filter: blur(15px); 
                box-shadow: 0 25px 50px rgba(0,0,0,0.8); text-align: center; color: white;
                margin: 40px 0;
            }}
            h2 {{ 
                margin-bottom: 25px; font-weight: 800; letter-spacing: 2px; 
                color: #fff; text-transform: uppercase; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);
            }}
            input, select {{ 
                width: 100%; padding: 14px; margin: 10px 0; border-radius: 12px; 
                border: 1px solid rgba(255, 255, 255, 0.2); background: rgba(255, 255, 255, 0.95); 
                color: #000; outline: none; font-size: 15px; transition: 0.3s; font-weight: 600;
            }}
            select:disabled {{ opacity: 0.6; cursor: not-allowed; }}
            input:focus {{ border-color: #00f2ff; box-shadow: 0 0 10px rgba(0,242,255,0.3); }}
            .oklad-info {{
                background: rgba(0, 242, 255, 0.15); padding: 15px;
                border: 1px solid #00f2ff; border-radius: 12px;
                margin: 15px 0; color: #00f2ff; font-weight: 900; font-size: 18px;
                display: flex; justify-content: space-between; align-items: center;
            }}
            .btn {{ 
                width: 100%; padding: 16px; border-radius: 14px; border: none; 
                background: #00f2ff; color: #000; font-weight: 900; cursor: pointer; 
                transition: 0.3s; text-transform: uppercase; margin-top: 15px; letter-spacing: 1px;
            }}
            .btn:hover {{ transform: scale(1.02); box-shadow: 0 5px 20px rgba(0, 242, 255, 0.5); }}
            label {{ 
                display: block; text-align: left; font-size: 11px; color: #00f2ff; 
                margin-left: 10px; text-transform: uppercase; margin-top: 10px; font-weight: bold;
            }}
            select option {{ background: #fff; color: #000; }}
        </style>
    </head>
    <body>
        <video loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="container">
            <h2><i class="fas fa-user-plus"></i> Ro'yxatdan o'tish</h2>
            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">

                <input type="text" name="full_name" placeholder="Ism-familiya" required>
                <input type="text" name="u_name" placeholder="Login yaratish" required>
                <input type="password" name="p_val" placeholder="Parol yarating" required>
                <input type="text" name="t_raqam" placeholder="Tabel raqami" required>
                <input type="text" name="tel_val" placeholder="Telefon (+998...)" required>

                <label>Otryadni tanlang:</label>
                <select id="otryad_select" onchange="updateGroups()" required>
                    <option value="" disabled selected>Ro'yxatdan tanlang</option>
                    {otryad_options}
                </select>

                <label>Guruhni tanlang:</label>
                <select id="guruh_select" name="guruh_id" disabled required>
                    <option value="" disabled selected>Avval otryadni tanlang</option>
                </select>

                <label>Razryad:</label>
                <input type="text" id="razryad" name="razryad" placeholder="Masalan: 5/3" oninput="calc()" required>

                <div class="oklad-info">
                    <span style="font-size: 13px; opacity: 0.8;">TARIF STAVKA:</span>
                    <span id="res">0 so'm</span>
                </div>

                <button type="submit" class="btn">HISOB YARATISH</button>
            </form>
            <p style="margin-top: 20px; font-size: 14px; color: rgba(255,255,255,0.8); font-weight: 500;">
                Profilingiz bormi? <a href="../" style="color: #00f2ff; text-decoration: none; font-weight: 900;">KIRISH</a>
            </p>
        </div>

        <script>
            const guruhlarData = {guruhlar_json};

            function updateGroups() {{
                const otryadId = document.getElementById('otryad_select').value;
                const guruhSelect = document.getElementById('guruh_select');

                guruhSelect.innerHTML = '<option value="" disabled selected>Guruhni tanlang</option>';

                if (otryadId && guruhlarData[otryadId]) {{
                    guruhSelect.disabled = false;
                    guruhlarData[otryadId].forEach(g => {{
                        const opt = document.createElement('option');
                        opt.value = g.id;
                        opt.textContent = g.nomi;
                        guruhSelect.appendChild(opt);
                    }});
                }} else {{
                    guruhSelect.disabled = true;
                }}
            }}

            function calc() {{
                const val = document.getElementById('razryad').value;
                const res = document.getElementById('res');
                const prices = {{"5/3": 5336929, "5/2": 4800000, "4/3": 4100000}};
                if (prices[val]) {{
                    res.innerText = prices[val].toLocaleString('fr-FR') + " so'm";
                }} else {{
                    res.innerText = "0 so'm";
                }}
            }}

            const video = document.getElementById('bg-video');
            window.addEventListener('load', () => {{
                video.muted = true;
                video.play().catch(e => console.log("Video autoplay blocked"));
            }});

            document.body.addEventListener('click', () => {{
                if (video.muted) {{ video.muted = false; }}
            }}, {{ once: true }});
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def verify_code_view(request):
    login_val = request.GET.get('login') or request.POST.get('login')
    user = UserProfile.objects.filter(login=login_val).first()

    if request.method == "POST":
        entered_code = request.POST.get('activation_code')
        if user and user.activation_code == entered_code:
            user.is_active = True
            user.save()
            request.session['user_login'] = user.login
            return redirect('/second/')
        else:
            return HttpResponse(
                "<h3 style='color:red; text-align:center; background:#000; height:100vh; margin:0; padding-top:20px;'>❌ Xato kod kiritildi! <br><a href='javascript:history.back()' style='color:white;'>Orqaga qaytish</a></h3>")

    # Resurslar
    video_url = static('uzb.mp4')
    token = get_token(request)

    html = f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aktivlashtirish | TemirYo'l</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ 
                margin: 0; height: 100vh; display: flex; 
                justify-content: center; align-items: center; 
                background: #000; font-family: 'Segoe UI', sans-serif; 
                overflow: hidden; 
            }}

            /* VIDEO FON */
            #bg-video {{
                position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%;
                z-index: -2; object-fit: cover;
            }}

            .overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.7); z-index: -1;
            }}

            .card {{ 
                background: rgba(255,255,255,0.08); 
                backdrop-filter: blur(20px); 
                padding: 35px 25px; 
                border-radius: 35px; 
                width: 90%; max-width: 350px; 
                text-align: center; 
                border: 1px solid rgba(255,255,255,0.15); 
                color: white; 
                box-shadow: 0 20px 50px rgba(0,0,0,0.6);
            }}

            .bot-btn {{ 
                display: flex; align-items: center; justify-content: center; gap: 10px;
                background: #0088cc; color: white; padding: 14px; 
                border-radius: 18px; text-decoration: none; 
                margin-bottom: 25px; font-weight: bold; 
                transition: 0.3s;
            }}
            .bot-btn:hover {{ transform: scale(1.02); background: #0099e6; }}

            input {{ 
                width: 100%; padding: 15px; border-radius: 18px; 
                border: 1px solid rgba(255,255,255,0.1); 
                background: rgba(255,255,255,0.1); color: white; 
                margin-bottom: 15px; box-sizing: border-box; 
                text-align: center; font-size: 22px; letter-spacing: 8px; 
                outline: none;
            }}
            input:focus {{ border-color: #00f2ff; background: rgba(255,255,255,0.15); }}
            input::placeholder {{ letter-spacing: normal; font-size: 15px; color: rgba(255,255,255,0.4); }}

            button {{ 
                width: 100%; padding: 15px; border-radius: 18px; border: none; 
                background: linear-gradient(135deg, #00f2ff, #0072ff); 
                color: #fff; font-weight: bold; cursor: pointer; 
                text-transform: uppercase; letter-spacing: 1px;
                transition: 0.3s;
            }}
            button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4); }}

            .info {{ font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 20px; line-height: 1.5; }}
            h3 {{ margin: 10px 0; font-weight: 300; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <video autoplay muted loop playsinline id="bg-video">
            <source src="{video_url}" type="video/mp4">
        </video>
        <div class="overlay"></div>

        <div class="card">
            <i class="fas fa-shield-alt" style="font-size: 50px; color: #00f2ff; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(0,242,255,0.5));"></i>
            <h3>Aktivlashtirish</h3>
            <p class="info">Profilingiz hozirda faolsiz. Uni faollashtirish uchun botdan olingan maxfiy kodni kiriting.</p>

            <a href="https://t.me/ReGiStRaTsIyATY_bot" class="bot-btn">
                <i class="fab fa-telegram-plane"></i> BOTDAN KOD OLISH
            </a>

            <form method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="{token}">
                <input type="hidden" name="login" value="{login_val}">
                <input type="text" name="activation_code" placeholder="KODNI YOZING" required maxlength="6">
                <button type="submit">TASDIQLASH</button>
            </form>

            <p style="margin-top: 20px; font-size: 12px; color: rgba(255,255,255,0.4);">
                Login: <b>{login_val}</b>
            </p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
def hisobot(request):
    user_login = request.session.get('user_login')
    if not user_login:
        return redirect('/')

    current_user = UserProfile.objects.filter(login=user_login).first()
    if not current_user:
        return redirect('/')

    # Ma'lumotlarni olish
    jadval_malumotlari = WorkSchedule.objects.filter(user=current_user).order_by('-date')

    # Jami hisoblash
    jami = jadval_malumotlari.aggregate(
        t_ish=Sum('ishlagan_soati'),
        t_tungi=Sum('tungi_soati'),
        t_bayram=Sum('bayram_soati')
    )

    video_url = static('uzb.mp4')

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hisobot | {current_user.login}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                * {{ box-sizing: border-box; }}
                body {{ 
                    margin: 0; padding: 20px; 
                    background: #000; color: white; 
                    font-family: 'Segoe UI', sans-serif; 
                    min-height: 100vh; overflow-x: hidden;
                }}

                /* VIDEO FON - MARKAZLASHTIRILGAN */
                #bg-video {{
                    position: fixed; top: 50%; left: 50%; min-width: 100%; min-height: 100%;
                    z-index: -2; transform: translate(-50%, -50%); object-fit: cover;
                }}
                .overlay {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0, 0, 0, 0.6); z-index: -1;
                }}

                .header {{ 
                    display: flex; align-items: center; justify-content: space-between; 
                    margin-bottom: 25px; position: relative; z-index: 10;
                    padding: 10px;
                }}
                .back-btn {{ 
                    background: rgba(0, 242, 255, 0.1); width: 45px; height: 45px; 
                    display: flex; align-items: center; justify-content: center; 
                    border-radius: 15px; color: #00f2ff; text-decoration: none; 
                    border: 1px solid rgba(0,242,255,0.4); transition: 0.3s;
                }}
                .back-btn:hover {{ background: #00f2ff; color: #000; transform: scale(1.05); }}

                .table-container {{ 
                    overflow-x: auto; 
                    background: rgba(0, 0, 0, 0.5); 
                    backdrop-filter: blur(15px); 
                    border-radius: 25px; 
                    border: 1px solid rgba(0, 242, 255, 0.2);
                    box-shadow: 0 15px 35px rgba(0,0,0,0.7);
                    position: relative; z-index: 1;
                    animation: fadeIn 0.8s ease-in-out;
                }}

                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(20px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}

                table {{ width: 100%; border-collapse: collapse; min-width: 600px; }}
                th {{ 
                    background: rgba(0, 242, 255, 0.15); 
                    color: #00f2ff; padding: 18px 10px; 
                    font-size: 12px; text-transform: uppercase; 
                    letter-spacing: 1px; border-bottom: 2px solid rgba(0,242,255,0.4);
                }}
                td {{ padding: 15px 10px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 14px; font-weight: 500; }}

                .date-col {{ color: #00f2ff; font-weight: bold; }}

                .total-row {{ 
                    background: rgba(0, 242, 255, 0.2); 
                    font-weight: 900; color: #fff; 
                    border-top: 2px solid #00f2ff; 
                }}

                /* Skrollbar stili */
                .table-container::-webkit-scrollbar {{ height: 6px; }}
                .table-container::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <video loop playsinline id="bg-video">
                <source src="{video_url}" type="video/mp4">
            </video>
            <div class="overlay"></div>

            <div class="header">
                <a href="/second/" class="back-btn"><i class="fas fa-arrow-left"></i></a>
                <h2 style="margin:0; font-weight:800; letter-spacing:1px; text-transform:uppercase;">Ish <span style="color:#00f2ff;">Hisoboti</span></h2>
                <div style="width:45px;"></div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Sana</th>
                            <th>Norma</th> 
                            <th>Oklad</th>
                            <th>Ishlangan</th>
                            <th>Tungi</th>
                            <th>Bayram</th>
                        </tr>
                    </thead>
                    <tbody>
        """

    last_oklad = 0
    last_norma = 0

    if jadval_malumotlari.exists():
        for row in jadval_malumotlari:
            last_oklad = row.oklad
            last_norma = row.norma_soati
            html += f"""
                    <tr>
                        <td class="date-col">{row.date}</td>
                        <td>{row.norma_soati}</td>
                        <td>{row.oklad:,.0f}</td>
                        <td>{row.ishlagan_soati}</td>
                        <td>{row.tungi_soati}</td>
                        <td>{row.bayram_soati}</td>
                    </tr>
                """

        # JAMI QATORI
        html += f"""
                    <tr class="total-row">
                        <td style="color:#00f2ff; text-transform:uppercase;">Jami:</td>
                        <td>{last_norma}</td>
                        <td>{last_oklad:,.0f}</td>
                        <td>{jami['t_ish'] or 0}</td>
                        <td>{jami['t_tungi'] or 0}</td>
                        <td>{jami['t_bayram'] or 0}</td>
                    </tr>
            """
    else:
        html += "<tr><td colspan='6' style='padding:80px; font-style:italic; color:rgba(255,255,255,0.4);'>Ma'lumotlar hozircha mavjud emas</td></tr>"

    html += """
                    </tbody>
                </table>
            </div>

            <script>
                const video = document.getElementById('bg-video');

                window.addEventListener('load', () => {
                    video.muted = false;
                    video.volume = 0.5;
                    let playPromise = video.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(() => {
                            video.muted = true;
                            video.play();
                        });
                    }
                });

                document.body.addEventListener('click', () => {
                    if (video.muted) {
                        video.muted = false;
                        video.play();
                    }
                }, { once: false });
            </script>
        </body>
        </html>
    """
    return HttpResponse(html)
