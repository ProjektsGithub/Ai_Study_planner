"""
Email Service — Mot de passe oublié
Supporte SMTP réel ou mode dev (log dans la console)
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service d'envoi d'emails transactionnels."""

    def __init__(self):
        self.smtp_host: Optional[str] = getattr(settings, "SMTP_HOST", None)
        self.smtp_port: int = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user: Optional[str] = getattr(settings, "SMTP_USER", None)
        self.smtp_password: Optional[str] = getattr(settings, "SMTP_PASSWORD", None)
        self.smtp_from: str = getattr(settings, "SMTP_FROM", "noreply@aiplanning.local")
        self.frontend_url: str = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

    def _is_configured(self) -> bool:
        """Vérifie si le SMTP est configuré."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def send_password_reset_email(self, recipient_email: str, recipient_name: str, reset_token: str) -> bool:
        """
        Envoie l'email de réinitialisation du mot de passe.

        Args:
            recipient_email: Adresse email du destinataire
            recipient_name:  Nom complet du destinataire
            reset_token:     Token sécurisé de réinitialisation

        Returns:
            True si l'envoi a réussi (ou mode dev), False sinon
        """
        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"

        if not self._is_configured():
            # Mode développement — afficher le lien dans les logs
            logger.warning("⚠️  SMTP non configuré — mode développement actif.")
            logger.info("=" * 60)
            logger.info("📧 EMAIL DE RÉINITIALISATION (MODE DEV)")
            logger.info(f"   Destinataire : {recipient_email}")
            logger.info(f"   Lien de reset : {reset_link}")
            logger.info("=" * 60)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Réinitialisation de votre mot de passe — AI Study Planner"
            msg["From"] = self.smtp_from
            msg["To"] = recipient_email

            # Version texte brut
            text_body = f"""Bonjour {recipient_name},

Vous avez demandé la réinitialisation de votre mot de passe.
Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe (valable 1 heure) :

{reset_link}

Si vous n'avez pas fait cette demande, ignorez cet email. Votre mot de passe ne changera pas.

L'équipe AI Study Planner
"""

            # Version HTML
            html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0a0a14;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="520" cellpadding="0" cellspacing="0" style="background:#12121f;border:1px solid rgba(99,102,241,0.25);border-radius:20px;overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:36px;text-align:center;">
              <div style="font-size:40px;margin-bottom:12px;">✦</div>
              <h1 style="color:#fff;margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px;">AI Study Planner</h1>
              <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:14px;">Réinitialisation du mot de passe</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <p style="color:rgba(255,255,255,0.8);font-size:15px;line-height:1.7;margin:0 0 20px;">
                Bonjour <strong style="color:#fff;">{recipient_name}</strong>,
              </p>
              <p style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.7;margin:0 0 28px;">
                Vous avez demandé la réinitialisation de votre mot de passe.
                Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe.
                Ce lien est valable pendant <strong style="color:#a78bfa;">1 heure</strong>.
              </p>
              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                <tr>
                  <td align="center" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;padding:14px 32px;">
                    <a href="{reset_link}" style="color:#fff;font-size:15px;font-weight:700;text-decoration:none;display:block;">
                      Réinitialiser mon mot de passe
                    </a>
                  </td>
                </tr>
              </table>
              <!-- Fallback link -->
              <p style="color:rgba(255,255,255,0.4);font-size:12px;line-height:1.6;margin:0 0 8px;">
                Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
              </p>
              <p style="word-break:break-all;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:8px;padding:10px 14px;margin:0 0 24px;">
                <a href="{reset_link}" style="color:#818cf8;font-size:12px;text-decoration:none;">{reset_link}</a>
              </p>
              <!-- Security note -->
              <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.25);border-radius:10px;padding:14px 16px;">
                <p style="color:rgba(245,158,11,0.9);font-size:12px;margin:0;line-height:1.6;">
                  🔒 Si vous n'avez pas fait cette demande, ignorez cet email.
                  Votre mot de passe actuel restera inchangé.
                </p>
              </div>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
              <p style="color:rgba(255,255,255,0.25);font-size:11px;margin:0;">
                © 2026 AI Study Planner · Cet email a été envoyé automatiquement, ne pas répondre.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, recipient_email, msg.as_string())

            logger.info(f"Email de réinitialisation envoyé à {recipient_email}")
            return True

        except Exception as exc:
            logger.error(f"Échec envoi email reset à {recipient_email}: {exc}")
            return False
