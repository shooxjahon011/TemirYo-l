from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.templatetags.static import static

from .models import UserProfile, IshHaqi
from .forms import RegistrationForm
def second_view(request):
    user_login = request.session.get('user_login', 'Mehmon')
    user = UserProfile.objects.filter(login=user_login).first()

    # Rasm manzillarini shakllantirish
    bg_url = static('image.jpg')
    avatar_url = user.image.url if user and user.image else static('default_avatar.png')
    display_name = user.login if user else "Mehmon"

    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <title>Bosh Menyu</title>
            <style>
                body, html {{ margin: 0; padding: 0; height: 100%; width: 100%; font-family: sans-serif; overflow: hidden; }}

                /* ORQA FON */
                .main-bg {{
                    position: fixed;
                    top: 0; left: 0; width: 100%; height: 100%;
                    /* Rasm yo'lini tekshirish uchun linear-gradient bilan birlashtirdik */
                    background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{bg_url}");
                    background-size: cover;
                    background-position: center;
                    z-index: -1;
                }}

                .profile-btn {{
                    position: absolute; top: 20px; right: 20px;
                    display: flex; align-items: center; color: white;
                    background: rgba(255,255,255,0.1); padding: 5px 15px;
                    border-radius: 30px; border: 1px solid rgba(255,255,255,0.3);
                    text-decoration: none; backdrop-filter: blur(10px);
                }}

                .profile-btn img {{ width: 35px; height: 35px; border-radius: 50%; margin-right: 10px; border: 2px solid #00f2ff; }}

                .container {{
                    display: flex; justify-content: center; align-items: center; height: 100vh;
                }}

                .menu-box {{
                    background: rgba(255,255,255,0.05); padding: 40px;
                    border-radius: 30px; text-align: center; width: 320px;
                    backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                }}

                h1 {{ color: #00f2ff; letter-spacing: 3px; font-size: 20px; margin-bottom: 30px; }}

                .nav-link {{
                    display: block; padding: 15px; margin: 15px 0;
                    background: rgba(255,255,255,0.1); color: white;
                    text-decoration: none; border-radius: 20px; font-weight: bold;
                    transition: 0.3s; border: 1px solid rgba(255,255,255,0.1);
                }}

                .nav-link:hover {{ background: #00f2ff; color: black; transform: scale(1.05); }}

                .exit {{ color: #ff4747; border-color: rgba(255,71,71,0.3); }}
                .exit:hover {{ background: #ff4747; color: white; }}
            </style>
        </head>
        <body>
            <div class="main-bg"></div>

            <a href="/profile/" class="profile-btn">
                <img src="{avatar_url}">
                <span>{display_name}</span>
            </a>

            <div class="container">
                <div class="menu-box">
                    <h1>BOSH MENYU</h1>
                    <a href="/Conculator/" class="nav-link">Oylik Hisoblash</a>
                    <a href="/soatlar/" class="nav-link">Kunlik Mashrut</a>
                    <a href="/profile/" class="nav-link">Sozlamalar</a>
                    <a href="/" class="nav-link exit">Chiqish</a>
                </div>
            </div>
        </body>
        </html>
        """
    return HttpResponse(html)
def profile_view(request):
    user_login = request.session.get('user_login')
    print(f"Sessiyadagi foydalanuvchi: {user_login}")  # Konsolda tekshirish uchun

    user = UserProfile.objects.filter(login=user_login).first()

    if not user:
        # Agar session bo'sh bo'lsa, bu yerga tushadi
        return redirect('/')
    # Bu yerda session yoki boshqa usul bilan foydalanuvchini aniqlash kerak
    # Misol uchun login qilingan foydalanuvchini login nomi orqali olamiz:

    if request.method == "POST":
        new_name = request.POST.get('display_name')
        new_pic = request.FILES.get('profile_pic')

        if new_name:
            user.login = new_name  # Ismni yangilash
        if new_pic:
            user.image = new_pic  # Rasmni yangilash

        user.save()
        request.session['user_login'] = user.login  # Sessionni ham yangilaymiz
        return redirect('/profile/')

    # Rasm bo'lsa o'sha rasm, bo'lmasa standart rasm
    avatar_url = user.image.url if user.image else static('default_avatar.png')
    bg_url = static('image.jpg')
    # Agar user obyekti va rasm mavjud bo'lsa user.image.url ni oladi
    if user and user.image:
        avatar_url = user.image.url
    else:
        avatar_url = "/static/default_avatar.png"  # yoki static('default_avatar.png')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Profil | {user.login}</title>
        <style>
            body {{ margin: 0; height: 100vh; display: flex; justify-content: center; align-items: center; background: #000; font-family: 'Segoe UI', sans-serif; color: white; }}
            .bg-image {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-image: url('{bg_url}'); background-size: cover; filter: brightness(0.3); z-index: -1; }}

            .profile-card {{
                background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
                padding: 40px; border-radius: 40px; width: 380px; text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            }}
            .avatar-container {{ position: relative; width: 120px; height: 120px; margin: 0 auto 20px; }}
            .avatar {{ width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 3px solid #00f2ff; box-shadow: 0 0 15px rgba(0, 242, 255, 0.5); }}

            .upload-btn {{
                position: absolute; bottom: 0; right: 0; background: #00f2ff; color: #000;
                width: 35px; height: 35px; border-radius: 50%; display: flex; justify-content: center;
                align-items: center; cursor: pointer; font-size: 20px; font-weight: bold;
            }}

            h2 {{ color: #00f2ff; margin: 10px 0; letter-spacing: 1px; }}
            .tabel-label {{ color: rgba(255, 255, 255, 0.5); font-size: 14px; margin-bottom: 25px; display: block; }}

            .input-group {{ text-align: left; margin-bottom: 20px; }}
            label {{ font-size: 12px; color: #00f2ff; margin-left: 15px; }}
            input[type="text"] {{
                width: 100%; padding: 12px 20px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.05); color: #fff; outline: none; box-sizing: border-box; margin-top: 5px;
            }}

            .save-btn {{
                width: 100%; padding: 14px; border-radius: 25px; border: none;
                background: #00f2ff; color: #000; font-weight: bold; cursor: pointer; transition: 0.3s;
            }}
            .save-btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0, 242, 255, 0.4); }}

            .back-link {{ display: block; margin-top: 20px; color: #aaa; text-decoration: none; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="bg-image"></div>
        <div class="profile-card">
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">

                <div class="avatar-container">
                    <img src="{avatar_url}" class="avatar" id="preview">
                    <label for="file-upload" class="upload-btn">+</label>
                    <input id="file-upload" name="profile_pic" type="file" style="display:none;" onchange="previewImage(this)">
                </div>

                <h2>{user.login}</h2>
                <span class="tabel-label">Tabel raqami: {user.tabel_raqami}</span>

                <div class="input-group">
                    <label>Ismni o'zgartirish:</label>
                    <input type="text" name="display_name" placeholder="Yangi ism kiriting" value="{user.login}">
                </div>

                <button type="submit" class="save-btn">SAQLASH</button>
            </form>

            <a href="/second/" class="back-link">← Asosiy sahifaga qaytish</a>
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
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)
def Hi_view(request):
        # Formadan ma'lumotlarni backenddagi o'zgaruvchilarga mos nom bilan olamiz
        salary = request.GET.get('salary')
        norma_soat = request.GET.get('norma_soat')
        ishlangan_soat = request.GET.get('ishlangan_soat')
        tungi_soat = request.GET.get('tungi_soat', 0)
        bayram_soati = request.GET.get('bayram_soati', 0)

        natija_html = ""

        if salary and norma_soat and ishlangan_soat:
            try:
                s = float(salary)
                n_s = float(norma_soat)
                i_s = float(ishlangan_soat)
                t_s = float(tungi_soat) if tungi_soat else 0
                b_s = float(bayram_soati) if bayram_soati else 0

                m = s / n_s
                asosiy_ish_haqi = m * i_s
                tungi_jami_bonus = t_s * (m * 0.5)
                mukofot = asosiy_ish_haqi * 0.20
                pitaniye_jami = (490000 / n_s) * i_s
                bayram_puli = b_s * m

                jami_brutto = asosiy_ish_haqi + mukofot + tungi_jami_bonus + pitaniye_jami + bayram_puli
                soliqlar = jami_brutto * (0.12 + 0.01 + 0.001)
                qolgan_summa = jami_brutto - soliqlar

                natija_html = f"""
                    <div style="background: rgba(0, 242, 255, 0.1); border: 1px solid #00f2ff; padding: 20px; border-radius: 20px; margin-bottom: 25px; color: #fff; text-align: left;">
                        <h3 style="color: #00f2ff; margin-top: 0; text-align: center;">Hisob-kitob natijasi</h3>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Soliqlarsiz (Brutto):</span> <b>{jami_brutto:,.0f} so'm</b>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span>Jami soliqlar:</span> <b style="color: #ff4747;">-{soliqlar:,.0f} so'm</b>
                        </div>
                        <hr style="border: 0.5px solid rgba(255,255,255,0.1);">
                        <div style="text-align: center; margin-top: 15px;">
                            <span style="font-size: 14px; color: #ccc;">Qo'lga tegadigan summa:</span><br>
                            <b style="font-size: 24px; color: #00f2ff;">{qolgan_summa:,.0f} so'm</b>
                        </div>
                    </div>
                """
            except ZeroDivisionError:
                natija_html = "<div style='color: #ff4747; margin-bottom: 20px;'>Xatolik: Norma soat 0 bo'lishi mumkin emas!</div>"
            except ValueError:
                natija_html = "<div style='color: #ff4747; margin-bottom: 20px;'>Iltimos, faqat son kiriting!</div>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Oylik Hisoblash</title>
            <style>
                body {{
                    margin: 0; padding: 0; min-height: 100vh; font-family: 'Segoe UI', sans-serif;
                    background: #000; display: flex; justify-content: center; align-items: center;
                    color: #fff;
                }}
                .bg-image {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background-image: url('/static/image.jpg'); /* Rasm manzili */
                    background-size: cover; background-position: center;
                    filter: brightness(0.4); z-index: -1;
                }}
                .calc-container {{
                    background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
                    padding: 30px; border-radius: 30px; width: 90%; max-width: 400px;
                    border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                    margin: 20px 0;
                }}
                h1 {{ font-weight: 300; font-size: 20px; text-transform: uppercase; letter-spacing: 2px; text-align: center; color: #00f2ff; }}
                label {{ font-size: 12px; color: #ccc; margin-left: 10px; }}
                input {{
                    width: 100%; padding: 12px 15px; margin: 5px 0 15px 0; border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05);
                    color: #fff; box-sizing: border-box; outline: none; transition: 0.3s;
                }}
                input:focus {{ border-color: #00f2ff; background: rgba(255, 255, 255, 0.1); }}
                .btn-calc {{
                    width: 100%; padding: 14px; border-radius: 25px; border: none;
                    background: #00f2ff; color: #000; font-weight: bold; cursor: pointer;
                    transition: 0.3s; margin-bottom: 10px;
                }}
                .btn-calc:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4); }}
                .btn-back {{
                    width: 100%; padding: 10px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.2);
                    background: transparent; color: #fff; cursor: pointer; transition: 0.3s; font-size: 13px;
                }}
                .btn-back:hover {{ background: rgba(255,255,255,0.1); }}
            </style>
        </head>
        <body>
            <div class="bg-image"></div>
            <div class="calc-container">
                <h1>Oylikni Hisoblash</h1>

                {natija_html}

                <form method="GET">
                    <label>Norma oylik (Shtat):</label>
                    <input type="number" name="salary" step="any" required placeholder="Masalan: 4000000">

                    <label>Norma ish soati:</label>
                    <input type="number" name="norma_soat" step="any" required placeholder="Masalan: 160">

                    <label>Haqiqatda ishlangan soat:</label>
                    <input type="number" name="ishlangan_soat" step="any" required placeholder="Masalan: 168">

                    <label>Tungi soat:</label>
                    <input type="number" name="tungi_soat" step="any" value="0">

                    <label>Bayram soati:</label>
                    <input type="number" name="bayram_soati" step="any" value="0">

                    <button type="submit" class="btn-calc">HISOBLASH</button>
                </form>

                <button class="btn-back" onclick="window.location.href='/second/'">ORQAGA QAYTISH</button>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
def main_chek(request):
    # 1. Bazadan hozirgi foydalanuvchiga tegishli ma'lumotni qidiramiz
    ma_lumot = IshHaqi.objects.filter(user=request.user).first()

    # 2. Agar foydalanuvchi uchun admin ma'lumot kiritmagan bo'lsa
    if not ma_lumot:
        return HttpResponse("""
                <body style="background:#000; color:#fff; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
                    <div style="text-align:center; border:1px solid #333; padding:20px; border-radius:20px;">
                        <h2 style="color:#00f2ff;">Ma'lumot topilmadi</h2>
                        <p>Admin hali sizning tabel raqamingizga ma'lumot kiritmagan.</p>
                        <a href="/second/" style="color:#00f2ff; text-decoration:none;">Orqaga qaytish</a>
                    </div>
                </body>
            """)

    # 3. Agar ma'lumot bo'lsa, HTML dizayningizni chiqaramiz
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ish Varaqasi</title>
            <style>
                body {{
                    margin: 0; padding: 0; min-height: 100vh; font-family: 'Segoe UI', sans-serif;
                    background: #000; display: flex; justify-content: center; align-items: center;
                    color: #fff;
                }}
                .bg-image {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background-image: url('/static/image.jpg');
                    background-size: cover; background-position: center;
                    filter: brightness(0.4); z-index: -1;
                }}
                .card-container {{
                    background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
                    padding: 35px; border-radius: 35px; width: 90%; max-width: 450px;
                    border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.6);
                }}
                h2 {{
                    color: #00f2ff; text-align: center; font-weight: 300;
                    text-transform: uppercase; letter-spacing: 2px; margin-bottom: 25px;
                    border-bottom: 1px solid rgba(0, 242, 255, 0.3); padding-bottom: 15px;
                }}
                .info-row {{
                    display: flex; justify-content: space-between; padding: 12px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }}
                .info-label {{ color: #ccc; font-size: 14px; }}
                .info-value {{ font-weight: bold; color: #fff; }}

                .btn-group {{ margin-top: 30px; }}

                .btn {{
                    width: 100%; padding: 14px; border-radius: 25px; border: none;
                    font-weight: bold; cursor: pointer; transition: 0.3s; margin-bottom: 12px;
                    font-size: 14px; text-transform: uppercase;
                }}
                .btn-calc {{
                    background: #00f2ff; color: #000;
                }}
                .btn-calc:hover {{
                    box-shadow: 0 8px 20px rgba(0, 242, 255, 0.4); transform: translateY(-2px);
                }}
                .btn-back {{
                    background: transparent; color: #fff; border: 1px solid rgba(255,255,255,0.2);
                }}
                .btn-back:hover {{
                    background: rgba(255,255,255,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="bg-image"></div>
            <div class="card-container">
                <h2>Ish Varaqasi</h2>

                <div class="info-row">
                    <span class="info-label">Norma ish soati:</span>
                    <span class="info-value">{ma_lumot.norma_ish:,.1f} soat</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Oylik oklad:</span>
                    <span class="info-value">{ma_lumot.oklad:,.0f} so'm</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Tungi soatlar:</span>
                    <span class="info-value">{ma_lumot.tungi_soat:,.1f} soat</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Bayram soatlari:</span>
                    <span class="info-value">{ma_lumot.bayram_soat:,.1f} soat</span>
                </div>
                <div class="info-row" style="border-bottom: none;">
                    <span class="info-label">Haqiqiy ish vaqti:</span>
                    <span class="info-value" style="color: #00f2ff;">{ma_lumot.ishlangan_soat:,.1f} soat</span>
                </div>

                <div class="btn-group">
                    <button class="btn btn-calc" onclick="window.location.href='/Conculator/'">
                        Oylikni hisoblash
                    </button>
                    <button class="btn btn-back" onclick="window.location.href='/second/'">
                        Orqaga qaytish
                    </button>
                </div>
            </div>
        </body>
        </html>
        """
    return HttpResponse(html)

def login(request):
    error_message = ""
    bg_url = static('image.jpg')

    if request.method == "POST":
        u = request.POST.get('u_name')
        p = request.POST.get('p_val')

        # Bazadan foydalanuvchini qidiramiz
        user = UserProfile.objects.filter(login=u, password=p).first()

        if user:
            # SESSiyaga saqlash - bu eng muhim qism!
            request.session['user_login'] = user.login
            return redirect('/second/')
        else:
            error_message = '<p style="color: #ff4747; font-weight: bold; margin-bottom: 20px;">⚠️ Login yoki parol xato!</p>'

    # GET so'rovi bo'lganda yoki login xato bo'lganda quyidagi HTML qaytadi
    html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        margin: 0; height: 100vh; display: flex;
                        justify-content: center; align-items: center;
                        background-color: #000; font-family: 'Segoe UI', sans-serif;
                    }}
                    .bg-image {{
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-image: url('{bg_url}');
                        background-size: cover;
                        background-position: center;
                        filter: brightness(0.4);
                        z-index: -1;
                    }}
                    .login-container {{
                        background: rgba(255, 255, 255, 0.05);
                        backdrop-filter: blur(20px);
                        padding: 50px; border-radius: 40px; width: 350px;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.5);
                    }}
                    .neon-brand {{ color: #00f2ff; font-size: 24px; font-weight: 900; letter-spacing: 3px; margin-bottom: 30px; }}
                    input {{ width: 100%; padding: 14px; margin-bottom: 15px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: #fff; text-align: center; outline: none; box-sizing: border-box; }}
                    .login-btn {{ width: 100%; padding: 14px; border-radius: 25px; border: none; background: #ff4747; color: #fff; font-weight: bold; cursor: pointer; transition: 0.3s; }}
                    .login-btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(255, 71, 71, 0.4); }}
                    .extra-links a {{ color: rgba(255,255,255,0.5); text-decoration: none; display: block; margin-top: 15px; font-size: 13px; }}
                </style>
            </head>
            <body>
                <div class="bg-image"></div>
                <div class="login-container">
                    <div class="neon-brand">TEMIRYO'L</div>
                    {error_message}
                    <form method="POST">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
                        <input type="text" name="u_name" placeholder="Foydalanuvchi nomi" required>
                        <input type="password" name="p_val" placeholder="Parol" required>
                        <button type="submit" class="login-btn">TIZIMGA KIRISH</button>
                    </form>
                    <div class="extra-links">
                        <a href="/signup/">Hali Ro'yxatdan o'tmadingizmi? Registratsiya</a>
                        <a href="/newpassword/">Parolni unutdingizmi?</a>
                    </div>
                </div>
            </body>
            </html>
            """
    return HttpResponse(html)
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Ma'lumot avtomatik DB Browser-ga (bazaga) tushadi
            return render(request, 'success.html')  # Muvaffaqiyatli sahifa
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})
def signup(request):
    if request.method == "POST":
        u = request.POST.get('u_name')
        p = request.POST.get('p_val')
        t = request.POST.get('t_val')

        if u and p:
            # MA'LUMOTNI BAZAGA SAQLASH
            UserProfile.objects.create(login=u, password=p, tabel_raqami=t)
            return redirect('/')  # Login sahifasiga qaytish

        # HTML qismi (f-string yordamida CSRF tokenni joylashtiramiz)
    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Registratsiya | TemirYo'l</title>
            <style>
                body {{
                    margin: 0; padding: 0; height: 100vh;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #000;
                    display: flex; justify-content: center; align-items: center;
                    color: #fff;
                }}
                .bg-image {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background-image: url('/static/image.jpg'); /* O'zingizning rasmingiz */
                    background-size: cover; background-position: center;
                    filter: brightness(0.3); z-index: -1;
                }}
                .signup-card {{
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(20px);
                    padding: 40px; border-radius: 35px;
                    width: 350px; text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
                }}
                h2 {{
                    color: #00f2ff; text-transform: uppercase;
                    letter-spacing: 2px; margin-bottom: 25px; font-weight: 300;
                }}
                input {{
                    width: 100%; padding: 12px 15px; margin-bottom: 15px;
                    border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
                    background: rgba(255, 255, 255, 0.05); color: #fff;
                    outline: none; box-sizing: border-box; transition: 0.3s;
                }}
                input:focus {{
                    border-color: #00f2ff;
                    box-shadow: 0 0 10px rgba(0, 242, 255, 0.2);
                }}
                .btn-save {{
                    width: 100%; padding: 14px; border-radius: 25px; border: none;
                    background: #00f2ff; color: #000; font-weight: bold;
                    cursor: pointer; transition: 0.3s; text-transform: uppercase;
                }}
                .btn-save:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(0, 242, 255, 0.4);
                }}
                .back-link {{
                    display: block; margin-top: 20px; color: #aaa;
                    text-decoration: none; font-size: 13px;
                }}
                .back-link:hover {{ color: #fff; }}
            </style>
        </head>
        <body>
            <div class="bg-image"></div>
            <div class="signup-card">
                <h2>Ro'yxatdan o'tish</h2>
                <form method="POST">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">

                    <input type="text" name="u_name" placeholder="Login yarating" required>
                    <input type="password" name="p_val" placeholder="Murakkab parol" required>
                    <input type="text" name="t_val" placeholder="Tabel raqamingiz">

                    <button type="submit" class="btn-save">Saqlash va Kirish</button>
                </form>
                <a href="/" class="back-link">Akkauntingiz bormi? Kirish sahifasiga qaytish</a>
            </div>
        </body>
        </html>
        """
    return HttpResponse(html)
def password(request):
    html = f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Parolni tiklash | TemirYo'l</title>
            <style>
                body {{ 
                    margin: 0; padding: 0; height: 100vh;
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #000;
                    display: flex; justify-content: center; align-items: center;
                    color: #fff;
                }}
                .bg-image {{
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background-image: url('/static/image.jpg');
                    background-size: cover; background-position: center;
                    filter: brightness(0.35); z-index: -1;
                }}
                .reset-card {{
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(25px);
                    -webkit-backdrop-filter: blur(25px);
                    padding: 40px; border-radius: 35px;
                    width: 100%; max-width: 380px; text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
                    box-sizing: border-box;
                }}
                h2 {{ 
                    color: #00f2ff; text-transform: uppercase;
                    letter-spacing: 2px; margin-bottom: 25px; font-weight: 300;
                }}
                label {{ 
                    display: block; text-align: left; font-size: 12px;
                    color: #ccc; margin: 0 0 5px 15px;
                }}
                input {{ 
                    width: 100%; padding: 13px 20px; margin-bottom: 15px; 
                    border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.1); 
                    background: rgba(255, 255, 255, 0.07); color: #fff; 
                    outline: none; box-sizing: border-box; transition: 0.3s;
                    font-size: 15px;
                }}
                input:focus {{ 
                    border-color: #ff4747; 
                    box-shadow: 0 0 15px rgba(255, 71, 71, 0.2);
                }}
                .reset-btn {{ 
                    background: #ff4747; color: white; border: none; 
                    padding: 15px; width: 100%; cursor: pointer; 
                    border-radius: 30px; font-size: 15px; font-weight: bold;
                    transition: 0.4s; margin-top: 10px; text-transform: uppercase;
                }}
                .reset-btn:hover {{ 
                    background: #e03636; transform: translateY(-2px); 
                    box-shadow: 0 8px 20px rgba(255, 71, 71, 0.4); 
                }}
                .back-btn {{
                    display: inline-block; margin-top: 20px; color: #aaa;
                    text-decoration: none; font-size: 13px; transition: 0.3s;
                }}
                .back-btn:hover {{ color: #fff; }}
            </style>
        </head>
        <body>

        <div class="bg-image"></div>

        <div class="reset-card">
            <h2>Parolni tiklash</h2>
            <form id="resetForm">
                <label>Login:</label>
                <input type="text" id="login" placeholder="Loginingizni kiriting" required>

                <label>Tabel raqami:</label>
                <input type="number" id="tabel" placeholder="Tabel raqamingiz" required>

                <label>Yangi Parol:</label>
                <input type="password" id="newPass" placeholder="Kamida 6 ta belgi" required>

                <label>Tasdiqlash:</label>
                <input type="password" id="confirmPass" placeholder="Parolni qayta kiriting" required>

                <button type="submit" class="reset-btn">Parolni yangilash</button>
            </form>
            <a href="/" class="back-btn">Bekor qilish va qaytish</a>
        </div>

        <script>
            document.getElementById('resetForm').addEventListener('submit', function(e) {{
                e.preventDefault();

                const p1 = document.getElementById('newPass').value;
                const p2 = document.getElementById('confirmPass').value;

                if (p1 !== p2) {{
                    alert("⚠️ Xato: Parollar bir-biriga mos kelmadi!");
                    return;
                }}

                if (p1.length < 4) {{
                    alert("⚠️ Parol juda qisqa!");
                    return;
                }}

                alert("✅ Parol muvaffaqiyatli yangilandi!");
                window.location.href = '/'; 
            }});
        </script>

        </body>
        </html>
        """
    return HttpResponse(html)
