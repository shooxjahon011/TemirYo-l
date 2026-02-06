from django.db import models

class UserProfile(models.Model):
    login = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    tabel_raqami = models.CharField(max_length=20)
    # MANA SHU QATORNI QO'SHING:
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.login

from django.db import models
from django.contrib.auth.models import User

class IshHaqi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Xodim")
    tabel_raqam = models.CharField(max_length=20, unique=False, verbose_name="Tabel Raqami")
    norma_ish = models.FloatField(verbose_name="Norma ish soati")
    oklad = models.FloatField(verbose_name="Oylik oklad (so'm)")
    tungi_soat = models.FloatField(verbose_name="Tungi soatlar")
    bayram_soat = models.FloatField(verbose_name="Bayram soatlari")
    ishlangan_soat = models.FloatField(verbose_name="Haqiqiy ishlangan soat")

    def save(self, *args, **kwargs):
        # Agar bu yangi kiritilayotgan ma'lumot bo'lsa (pk yo'qligi shuni bildiradi)
        if not self.pk:
            # Ushbu foydalanuvchiga tegishli barcha eski ma'lumotlarni o'chirib tashlaymiz
            IshHaqi.objects.filter(user=self.user).delete()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.tabel_raqam}"