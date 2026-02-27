from django.db import models


# 1. Otryadlar (Masalan: 1-Otryad, 2-Otryad)
class Otryad(models.Model):
    nomi = models.CharField(max_length=255)

    def __str__(self):
        return self.nomi


# 2. Ishchi Guruhlar (Otryadga tegishli guruhlar)
class IshchiGuruh(models.Model):
    nomi = models.CharField(max_length=100)
    otryad = models.ForeignKey(Otryad, on_delete=models.CASCADE, related_name='guruhlar', null=True, blank=True)

    def __str__(self):
        return f"{self.nomi} ({self.otryad.nomi if self.otryad else 'Otryadsiz'})"


# 3. Foydalanuvchi Profili (Ishchi va Boshliqlar uchun)
class UserProfile(models.Model):
    full_name = models.CharField(max_length=255)
    login = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    tabel_raqami = models.CharField(max_length=50)

    # Izolyatsiya va Guruhlash
    is_boss = models.BooleanField(default=False)  # Boshliqlarni ajratish uchun
    otryad = models.ForeignKey(Otryad, on_delete=models.SET_NULL, null=True, blank=True)
    guruh = models.ForeignKey(IshchiGuruh, on_delete=models.SET_NULL, null=True, blank=True)

    # Manzil ma'lumotlari (Siz so'ragan barcha maydonlar)
    viloyat = models.CharField(max_length=100, blank=True, null=True)
    shahar_tuman = models.CharField(max_length=100, blank=True, null=True)
    mahalla = models.CharField(max_length=100, blank=True, null=True)
    kocha = models.CharField(max_length=100, blank=True, null=True)
    uy_raqami = models.CharField(max_length=20, blank=True, null=True)

    # Ish ma'lumotlari
    razryad = models.CharField(max_length=10, blank=True, null=True)
    oklad = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Jonli lokatsiya (Oxirgi turgan joyi)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Xavfsizlik va holat
    activation_code = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_working = models.BooleanField(default=False)  # Ish holati
    work_start_time = models.DateTimeField(null=True, blank=True)  #

    def __str__(self):
        role = "Boshliq" if self.is_boss else "Ishchi"
        return f"{self.full_name} ({role} - {self.tabel_raqami})"


# 4. 24 Soatlik Lokatsiya Tarixi (Marshrutni chizish uchun)
class LocationHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='history')
    lat = models.FloatField()
    lng = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']  # Oxirgi nuqtalar birinchi chiqadi


# 5. Chat tizimi (Guruh bo'yicha ajratilgan)
class ChatMessage(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    guruh = models.ForeignKey(IshchiGuruh, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    video = models.FileField(upload_to='chat_videos/', null=True, blank=True)
    voice = models.FileField(upload_to='chat_voices/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.login} xabari ({self.created_at})"


# 6. Ish jadvali (Tabel)
class WorkSchedule(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField()
    oklad = models.FloatField(default=0)
    norma_soati = models.FloatField(default=0)
    ishlagan_soati = models.FloatField(default=0)
    tungi_soati = models.FloatField(default=0)
    bayram_soati = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.login} - {self.date}"
