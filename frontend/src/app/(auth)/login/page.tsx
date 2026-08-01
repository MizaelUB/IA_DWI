'use client';

import { useState, useEffect, FormEvent, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { PawIcon } from '@/components/ui/Icons';
import { Modal } from '@/components/ui/Modal';

type AuthMode = 'login' | 'register' | 'recovery';

interface FormErrors {
  [key: string]: string;
}

export default function AuthPage() {
  const { user, isLoading, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── Mode toggle ──
  const [mode, setMode] = useState<AuthMode>((searchParams.get('mode') as AuthMode) || 'login');

  // ── Login state ──
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [loginCaptchaData, setLoginCaptchaData] = useState<{ id: string; question?: string; img1?: string; img2?: string; operator?: string } | null>(null);
  const [loginCaptchaAnswer, setLoginCaptchaAnswer] = useState('');

  // ── Register state ──
  const [regSubmitting, setRegSubmitting] = useState(false);
  const [regError, setRegError] = useState('');
  const [regSuccess, setRegSuccess] = useState('');
  const [regErrors, setRegErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<FormErrors>({});

  // ── Recovery state ──
  const [recoveryEmail, setRecoveryEmail] = useState('');
  const [recoveryError, setRecoveryError] = useState('');
  const [recoverySubmitting, setRecoverySubmitting] = useState(false);
  const [recoverySuccess, setRecoverySuccess] = useState('');
  
  // ── Reset password modal ──
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetSubmitting, setResetSubmitting] = useState(false);
  const [resetError, setResetError] = useState('');

  // ── Verification modal ──
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [verifySubmitting, setVerifySubmitting] = useState(false);
  const [verifyError, setVerifyError] = useState('');

  // Register fields
  const [doctorLicense, setDoctorLicense] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [vetName, setVetName] = useState('');
  const [vetCity, setVetCity] = useState('');
  const [vetAddress, setVetAddress] = useState('');
  const [vetPhone, setVetPhone] = useState('');
  const [vetEmail, setVetEmail] = useState('');

  useEffect(() => {
    if (!isLoading && user) router.replace('/asistente');
  }, [user, isLoading, router]);

  // ── CAPTCHA helpers ──
  const fetchCaptcha = async (setFn: (data: any) => void) => {
    try {
      const res = await fetch('/api/auth/captcha');
      const data = await res.json();
      setFn({ id: data.captcha_id, question: data.question, img1: data.img1, img2: data.img2, operator: data.operator });
    } catch {
      setLoginError('Error al cargar CAPTCHA');
    }
  };

  // ── Switch mode ──
  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setLoginError('');
    setRegError('');
    setRegSuccess('');
    setRegErrors({});
    setTouched({});
    setLoginCaptchaData(null);
    setLoginCaptchaAnswer('');
    setShowVerifyModal(false);
    setVerificationCode('');
    setVerifyError('');
    setRecoveryError('');
    setRecoverySuccess('');
    setShowResetModal(false);
    setResetCode('');
    setNewPassword('');
    setResetError('');
  };

  // ══════════════════════════════════════════
  //  LOGIN
  // ══════════════════════════════════════════
  const handleLoginSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!loginUsername.trim() || !loginPassword.trim()) return;
    setLoginError('');
    setLoginSubmitting(true);
    const result = await login(loginUsername.trim(), loginPassword.trim(), loginCaptchaData?.id, loginCaptchaAnswer);
    if (result.success) {
      router.push('/asistente');
    } else if (result.requiresCaptcha) {
      setLoginError(result.error || 'Resuelve el CAPTCHA para continuar.');
      await fetchCaptcha(setLoginCaptchaData);
      setLoginCaptchaAnswer('');
    } else {
      setLoginError(result.error || 'Error desconocido');
      if (loginCaptchaData) {
        await fetchCaptcha(setLoginCaptchaData);
        setLoginCaptchaAnswer('');
      }
    }
    setLoginSubmitting(false);
  };


  // ══════════════════════════════════════════
  //  REGISTER – field-level validation
  // ══════════════════════════════════════════
  const validateField = useCallback((name: string, value: string): string => {
    switch (name) {
      case 'doctorLicense':
        if (!value.trim()) return 'La cédula del médico es obligatoria.';
        if (!/^[a-zA-Z0-9]{6,20}$/.test(value)) return '6-20 caracteres alfanuméricos.';
        return '';
      case 'fullName':
        if (!value.trim()) return 'El nombre completo es obligatorio.';
        if (value.length < 2 || value.length > 100) return '2-100 caracteres.';
        return '';
      case 'email':
        if (!value.trim()) return 'El correo es obligatorio.';
        if (!/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(value)) return 'Correo electrónico no válido.';
        return '';
      case 'phone': {
        const clean = value.replace(/[\s\-\(\)]/g, '');
        if (!clean) return 'El teléfono es obligatorio.';
        if (!/^\d{10}$/.test(clean)) return 'Debe tener 10 dígitos.';
        return '';
      }
      case 'password':
        if (!value) return 'La contraseña es obligatoria.';
        if (value.length < 8) return 'Mínimo 8 caracteres.';
        if (!/[A-Z]/.test(value)) return 'Al menos una mayúscula.';
        if (!/[a-z]/.test(value)) return 'Al menos una minúscula.';
        if (!/[0-9]/.test(value)) return 'Al menos un número.';
        return '';
      case 'confirmPassword':
        if (value !== password) return 'Las contraseñas no coinciden.';
        return '';
      case 'vetName':
        if (!value.trim()) return 'El nombre de la veterinaria es obligatorio.';
        if (value.length < 2 || value.length > 100) return '2-100 caracteres.';
        return '';
      case 'vetCity':
        if (!value.trim()) return 'La ciudad es obligatoria.';
        if (value.length < 2 || value.length > 50) return '2-50 caracteres.';
        return '';
      default:
        return '';
    }
  }, [password]);

  const handleBlur = (name: string, value: string) => {
    setTouched((prev) => ({ ...prev, [name]: '1' }));
    const error = validateField(name, value);
    setRegErrors((prev) => {
      const next = { ...prev };
      if (error) next[name] = error;
      else delete next[name];
      return next;
    });
  };

  const handleChange = (name: string, value: string, setter: (v: string) => void) => {
    setter(value);
    if (touched[name]) {
      const error = validateField(name, value);
      setRegErrors((prev) => {
        const next = { ...prev };
        if (error) next[name] = error;
        else delete next[name];
        return next;
      });
    }
  };

  const validateAll = (): boolean => {
    const fields: [string, string][] = [
      ['doctorLicense', doctorLicense],
      ['fullName', fullName],
      ['email', email],
      ['phone', phone],
      ['password', password],
      ['confirmPassword', confirmPassword],
      ['vetName', vetName],
      ['vetCity', vetCity],
    ];
    const newErrors: FormErrors = {};
    const newTouched: FormErrors = {};
    for (const [name, value] of fields) {
      newTouched[name] = '1';
      const error = validateField(name, value);
      if (error) newErrors[name] = error;
    }
    setTouched(newTouched);
    setRegErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegisterSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setRegError('');
    setRegSuccess('');
    if (!validateAll()) return;
    setRegSubmitting(true);
    try {
      const res = await fetch('/api/auth/request-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          purpose: 'registro'
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setShowVerifyModal(true);
      } else {
        setRegError(data.detail || 'Error al solicitar código.');
      }
    } catch {
      setRegError('Error de conexión con el servidor.');
    } finally {
      setRegSubmitting(false);
    }
  };

  const confirmVerificationAndRegister = async () => {
    setVerifyError('');
    if (!verificationCode.trim() || verificationCode.length !== 6) {
      setVerifyError('Ingresa un código válido de 6 dígitos.');
      return;
    }
    setVerifySubmitting(true);
    try {
      // 1. Verificar el código
      const verifyRes = await fetch('/api/auth/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          code: verificationCode.trim(),
          purpose: 'registro'
        }),
      });
      const verifyData = await verifyRes.json();
      
      if (!verifyRes.ok) {
        setVerifyError(verifyData.detail || 'Código incorrecto o expirado.');
        setVerifySubmitting(false);
        return;
      }

      // 2. Si es válido, registrar
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          password,
          email: email.trim(),
          full_name: fullName.trim(),
          phone: phone.replace(/[\s\-\(\)]/g, ''),
          doctor_license: doctorLicense.trim(),
          vet_name: vetName.trim(),
          vet_city: vetCity.trim(),
          vet_address: vetAddress.trim(),
          vet_phone: vetPhone.trim(),
          vet_email: vetEmail.trim(),
        }),
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setShowVerifyModal(false);
        setRegSuccess(data.message || 'Registro exitoso. Tu veterinaria está pendiente de aprobación.');
      } else {
        setVerifyError(typeof data.detail === 'string' ? data.detail : 'Error al registrar.');
      }
    } catch {
      setVerifyError('Error de conexión con el servidor.');
    } finally {
      setVerifySubmitting(false);
    }
  };

  // ══════════════════════════════════════════
  //  RECOVERY
  // ══════════════════════════════════════════
  const handleRecoverySubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!recoveryEmail.trim()) return;
    setRecoveryError('');
    setRecoverySuccess('');
    setRecoverySubmitting(true);
    try {
      const res = await fetch('/api/auth/request-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: recoveryEmail.trim(),
          purpose: 'recuperacion'
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setRecoverySuccess(data.message || 'Si tu correo coincide con alguna cuenta, se enviará un código de verificación.');
        setShowResetModal(true);
      } else {
        setRecoveryError(data.detail || 'Error al solicitar recuperación.');
      }
    } catch {
      setRecoveryError('Error de conexión con el servidor.');
    } finally {
      setRecoverySubmitting(false);
    }
  };

  const confirmResetPassword = async () => {
    setResetError('');
    if (!resetCode.trim() || resetCode.length !== 6) {
      setResetError('Ingresa un código válido de 6 dígitos.');
      return;
    }
    if (newPassword.length < 8) {
      setResetError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    setResetSubmitting(true);
    try {
      const res = await fetch('/api/auth/reset-password-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: recoveryEmail.trim(),
          code: resetCode.trim(),
          new_password: newPassword
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setShowResetModal(false);
        switchMode('login');
        setLoginError('Contraseña actualizada exitosamente. Ahora puedes iniciar sesión.');
      } else {
        setResetError(data.detail || 'Código incorrecto o expirado.');
      }
    } catch {
      setResetError('Error de conexión con el servidor.');
    } finally {
      setResetSubmitting(false);
    }
  };

  if (isLoading || user) return null;

  // ── Success screen ──
  if (regSuccess) {
    return (
      <div className="login">
        <aside className="login-aside">
          <div className="login-aside-glow" aria-hidden="true" />
          <svg className="login-aside-paw" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 13.2c-2.4 0-4.3 1.7-4.3 3.8 0 1.1.9 1.8 2 1.8.9 0 1.5-.3 2.3-.3s1.4.3 2.3.3c1.1 0 2-.7 2-1.8 0-2.1-1.9-3.8-4.3-3.8Z"/><ellipse cx="6.7" cy="11" rx="1.6" ry="2"/><ellipse cx="17.3" cy="11" rx="1.6" ry="2"/><ellipse cx="9.7" cy="7.6" rx="1.5" ry="1.9"/><ellipse cx="14.3" cy="7.6" rx="1.5" ry="1.9"/></svg>
          <div className="login-aside-top">
            <span className="login-aside-mark"><PawIcon size={24} /></span>
            <span className="login-aside-name">Swingtails</span>
          </div>
          <div className="login-aside-body">
            <h2 className="login-aside-title">Gestion veterinaria</h2>
            <p className="login-aside-sub">Citas, pacientes y clientes en un solo panel.</p>
          </div>
          <p className="login-aside-foot">Panel para personal administrativo y veterinarios.</p>
        </aside>
        <main className="login-main">
          <div className="login-card">
            <div className="login-head">
              <h1 className="login-title">Solicitud Enviada</h1>
            </div>
            <div className="auth-success-box">
              <div className="auth-success-icon">&#10003;</div>
              <p className="auth-success-msg">{regSuccess}</p>
              <p className="auth-success-sub">
                Un administrador revisara tu solicitud y activara tu cuenta. Recibiras acceso una vez que tu veterinaria sea verificada.
              </p>
              <button onClick={() => switchMode('login')} className="btn btn-primary btn-block">
                Iniciar sesion
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // ── Field helper ──
  const fieldClass = (name: string) =>
    `field${regErrors[name] && touched[name] ? ' field--error' : ''}${touched[name] && !regErrors[name] ? ' field--valid' : ''}`;

  return (
    <div className="login">
      <aside className="login-aside">
        <div className="login-aside-glow" aria-hidden="true" />
        <svg className="login-aside-paw" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 13.2c-2.4 0-4.3 1.7-4.3 3.8 0 1.1.9 1.8 2 1.8.9 0 1.5-.3 2.3-.3s1.4.3 2.3.3c1.1 0 2-.7 2-1.8 0-2.1-1.9-3.8-4.3-3.8Z"/><ellipse cx="6.7" cy="11" rx="1.6" ry="2"/><ellipse cx="17.3" cy="11" rx="1.6" ry="2"/><ellipse cx="9.7" cy="7.6" rx="1.5" ry="1.9"/><ellipse cx="14.3" cy="7.6" rx="1.5" ry="1.9"/></svg>
        <div className="login-aside-top">
          <span className="login-aside-mark"><PawIcon size={24} /></span>
          <span className="login-aside-name">Swingtails</span>
        </div>
        <div className="login-aside-body">
          <h2 className="login-aside-title">Gestion veterinaria</h2>
          <p className="login-aside-sub">Citas, pacientes y clientes en un solo panel.</p>
        </div>
        <p className="login-aside-foot">Panel para personal administrativo y veterinarios.</p>
      </aside>

      <main className="login-main">
        <div className={`login-card${mode === 'register' ? ' login-card--wide' : ''}`}>

          {/* ── Toggle buttons ── */}
          <div className="auth-toggle">
            <button
              className={`auth-toggle-btn${mode === 'login' ? ' active' : ''}`}
              onClick={() => switchMode('login')}
              type="button"
            >
              Iniciar sesion
            </button>
            <button
              className={`auth-toggle-btn${mode === 'register' ? ' active' : ''}`}
              onClick={() => switchMode('register')}
              type="button"
            >
              Crear cuenta
            </button>
          </div>

          {/* ════════════════ LOGIN ════════════════ */}
          {mode === 'login' && (
            <>
              <div className="login-head">
                <h1 className="login-title">Bienvenido de vuelta</h1>
                <p className="login-subtitle">Accede al panel de Swingtails</p>
              </div>
              <form className="login-form" onSubmit={handleLoginSubmit} autoComplete="on">
                <div className="field">
                  <label htmlFor="login-email">Correo electronico o usuario</label>
                  <input
                    type="text"
                    id="login-email"
                    name="username"
                    placeholder="tu@veterinaria.com"
                    autoComplete="username"
                    required
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="login-password">Contrasena</label>
                  <input
                    type="password"
                    id="login-password"
                    name="password"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </div>

                {loginCaptchaData && (
                  <div className="field captcha-field">
                    <label>Resuelve la operacion:</label>
                    <div className="captcha-question">
                      Cuanto es{' '}
                      {loginCaptchaData.img1 && <img src={`data:image/png;base64,${loginCaptchaData.img1}`} alt="numero" className="captcha-img" />}
                      {loginCaptchaData.operator || 'x'}
                      {loginCaptchaData.img2 && <img src={`data:image/png;base64,${loginCaptchaData.img2}`} alt="numero" className="captcha-img" />}
                      ?
                    </div>
                    <input
                      type="text"
                      value={loginCaptchaAnswer}
                      onChange={(e) => setLoginCaptchaAnswer(e.target.value)}
                      className="captcha-input"
                      placeholder="Tu respuesta"
                      required
                    />
                  </div>
                )}

                <p className="login-error" role="alert">{loginError}</p>
                <div style={{ textAlign: 'right', marginBottom: '16px' }}>
                  <button type="button" onClick={() => switchMode('recovery')} style={{ background: 'none', border: 'none', color: 'var(--brand-primary)', cursor: 'pointer', fontSize: '0.9rem' }}>
                    ¿Olvidaste tu contraseña?
                  </button>
                </div>
                <button type="submit" className="btn btn-primary btn-block" disabled={loginSubmitting || (loginCaptchaData !== null && !loginCaptchaAnswer.trim())}>
                  {loginSubmitting ? 'Conectando...' : 'Iniciar sesion'}
                </button>
              </form>
            </>
          )}

          {/* ════════════════ REGISTER ════════════════ */}
          {mode === 'register' && (
            <>
              <div className="login-head">
                <h1 className="login-title">Crear cuenta</h1>
                <p className="login-subtitle">Registra tu veterinaria en Swingtails</p>
              </div>
              <form className="login-form login-form--register" onSubmit={handleRegisterSubmit} autoComplete="on">

                {/* Seccion: Medico */}
                <h3 className="form-section-title">Datos del medico encargado</h3>
                <div className={fieldClass('doctorLicense')}>
                  <label htmlFor="doctor-license">Cedula del medico *</label>
                  <input
                    type="text"
                    id="doctor-license"
                    placeholder="Ej. 12345678"
                    value={doctorLicense}
                    onChange={(e) => handleChange('doctorLicense', e.target.value, setDoctorLicense)}
                    onBlur={() => handleBlur('doctorLicense', doctorLicense)}
                  />
                  {regErrors.doctorLicense && touched.doctorLicense && <span className="field-error">{regErrors.doctorLicense}</span>}
                </div>

                {/* Seccion: Datos personales */}
                <h3 className="form-section-title">Datos personales</h3>
                <div className={fieldClass('fullName')}>
                  <label htmlFor="full-name">Nombre completo *</label>
                  <input
                    type="text"
                    id="full-name"
                    placeholder="Juan Perez Lopez"
                    value={fullName}
                    onChange={(e) => handleChange('fullName', e.target.value, setFullName)}
                    onBlur={() => handleBlur('fullName', fullName)}
                  />
                  {regErrors.fullName && touched.fullName && <span className="field-error">{regErrors.fullName}</span>}
                </div>
                <div className={fieldClass('email')}>
                  <label htmlFor="reg-email">Correo electronico *</label>
                  <input
                    type="email"
                    id="reg-email"
                    placeholder="juan@veterinaria.com"
                    value={email}
                    onChange={(e) => handleChange('email', e.target.value, setEmail)}
                    onBlur={() => handleBlur('email', email)}
                  />
                  {regErrors.email && touched.email && <span className="field-error">{regErrors.email}</span>}
                </div>
                <div className={fieldClass('phone')}>
                  <label htmlFor="reg-phone">Telefono *</label>
                  <input
                    type="tel"
                    id="reg-phone"
                    placeholder="10 digitos"
                    value={phone}
                    onChange={(e) => handleChange('phone', e.target.value, setPhone)}
                    onBlur={() => handleBlur('phone', phone)}
                  />
                  {regErrors.phone && touched.phone && <span className="field-error">{regErrors.phone}</span>}
                </div>
                <div className={fieldClass('password')}>
                  <label htmlFor="reg-password">Contrasena *</label>
                  <input
                    type="password"
                    id="reg-password"
                    placeholder="Minimo 8 caracteres"
                    value={password}
                    onChange={(e) => handleChange('password', e.target.value, setPassword)}
                    onBlur={() => handleBlur('password', password)}
                  />
                  {regErrors.password && touched.password && <span className="field-error">{regErrors.password}</span>}
                </div>
                <div className={fieldClass('confirmPassword')}>
                  <label htmlFor="reg-confirm-password">Confirmar contrasena *</label>
                  <input
                    type="password"
                    id="reg-confirm-password"
                    placeholder="Repite tu contrasena"
                    value={confirmPassword}
                    onChange={(e) => handleChange('confirmPassword', e.target.value, setConfirmPassword)}
                    onBlur={() => handleBlur('confirmPassword', confirmPassword)}
                  />
                  {regErrors.confirmPassword && touched.confirmPassword && <span className="field-error">{regErrors.confirmPassword}</span>}
                </div>

                {/* Seccion: Veterinaria */}
                <h3 className="form-section-title">Datos de la veterinaria</h3>
                <div className={fieldClass('vetName')}>
                  <label htmlFor="vet-name">Nombre de la veterinaria *</label>
                  <input
                    type="text"
                    id="vet-name"
                    placeholder="Clinica Veterinaria San Juan"
                    value={vetName}
                    onChange={(e) => handleChange('vetName', e.target.value, setVetName)}
                    onBlur={() => handleBlur('vetName', vetName)}
                  />
                  {regErrors.vetName && touched.vetName && <span className="field-error">{regErrors.vetName}</span>}
                </div>
                <div className={fieldClass('vetCity')}>
                  <label htmlFor="vet-city">Ciudad *</label>
                  <input
                    type="text"
                    id="vet-city"
                    placeholder="Ciudad de Mexico"
                    value={vetCity}
                    onChange={(e) => handleChange('vetCity', e.target.value, setVetCity)}
                    onBlur={() => handleBlur('vetCity', vetCity)}
                  />
                  {regErrors.vetCity && touched.vetCity && <span className="field-error">{regErrors.vetCity}</span>}
                </div>
                <div className="field">
                  <label htmlFor="vet-address">Direccion (opcional)</label>
                  <input
                    type="text"
                    id="vet-address"
                    placeholder="Calle, numero, colonia"
                    value={vetAddress}
                    onChange={(e) => setVetAddress(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="vet-phone">Telefono de la veterinaria (opcional)</label>
                  <input
                    type="tel"
                    id="vet-phone"
                    placeholder="Telefono del local"
                    value={vetPhone}
                    onChange={(e) => setVetPhone(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="vet-email">Correo de la veterinaria (opcional)</label>
                  <input
                    type="email"
                    id="vet-email"
                    placeholder="contacto@veterinaria.com"
                    value={vetEmail}
                    onChange={(e) => setVetEmail(e.target.value)}
                  />
                </div>

                <p className="login-error" role="alert">{regError}</p>
                <button type="submit" className="btn btn-primary btn-block" disabled={regSubmitting}>
                  {regSubmitting ? 'Registrando...' : 'Crear cuenta'}
                </button>
              </form>
            </>
          )}

          {/* ════════════════ RECOVERY ════════════════ */}
          {mode === 'recovery' && (
            <>
              <div className="login-head">
                <h1 className="login-title">Recuperar contraseña</h1>
                <p className="login-subtitle">Ingresa tu correo para recibir un código</p>
              </div>
              
              {recoverySuccess ? (
                <div className="auth-success-box">
                  <div className="auth-success-icon">&#10003;</div>
                  <p className="auth-success-msg">{recoverySuccess}</p>
                </div>
              ) : (
                <form className="login-form" onSubmit={handleRecoverySubmit} autoComplete="on">
                  <div className="field">
                    <label htmlFor="recovery-email">Correo electronico</label>
                    <input
                      type="email"
                      id="recovery-email"
                      placeholder="tu@veterinaria.com"
                      autoComplete="email"
                      required
                      value={recoveryEmail}
                      onChange={(e) => setRecoveryEmail(e.target.value)}
                    />
                  </div>
                  
                  <p className="login-error" role="alert">{recoveryError}</p>
                  
                  <button type="submit" className="btn btn-primary btn-block" disabled={recoverySubmitting}>
                    {recoverySubmitting ? 'Enviando...' : 'Enviar código'}
                  </button>
                  
                  <div className="auth-divider" style={{ marginTop: '24px' }}><span>o</span></div>
                  <button type="button" onClick={() => switchMode('login')} className="btn btn-ghost btn-block" disabled={recoverySubmitting}>
                    Volver a Iniciar sesión
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </main>



      {/* Verify Email Modal */}
      <Modal isOpen={showVerifyModal} onClose={() => setShowVerifyModal(false)} title="Verificar Correo Electrónico">
        <p style={{ marginBottom: '16px', color: 'var(--text-muted)' }}>
          Hemos enviado un código de verificación de 6 dígitos a <strong>{email}</strong>. Por favor, ingrésalo a continuación para continuar con tu registro.
        </p>
        
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)' }}>Código de Verificación *</label>
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="Ej. 123456"
            style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)', fontSize: '1rem' }}
          />
        </div>

        {verifyError && <p style={{ color: '#ef4444', marginBottom: '16px' }}>{verifyError}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button onClick={() => setShowVerifyModal(false)} className="btn btn-ghost" disabled={verifySubmitting}>Cancelar</button>
          <button onClick={confirmVerificationAndRegister} className="btn btn-primary" disabled={verifySubmitting || verificationCode.length !== 6}>
            {verifySubmitting ? 'Verificando...' : 'Verificar y Registrar'}
          </button>
        </div>
      </Modal>

      {/* Reset Password Modal */}
      <Modal isOpen={showResetModal} onClose={() => setShowResetModal(false)} title="Restablecer Contraseña">
        <p style={{ marginBottom: '16px', color: 'var(--text-muted)' }}>
          Si el correo existe en nuestro sistema, hemos enviado un código de verificación de 6 dígitos a <strong>{recoveryEmail}</strong>. Ingrésalo junto con tu nueva contraseña.
        </p>
        
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)' }}>Código de Verificación *</label>
          <input
            type="text"
            value={resetCode}
            onChange={(e) => setResetCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="Ej. 123456"
            style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)', fontSize: '1rem' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-main)' }}>Nueva Contraseña *</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Mínimo 8 caracteres"
            style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-main)', fontSize: '1rem' }}
          />
        </div>

        {resetError && <p style={{ color: '#ef4444', marginBottom: '16px' }}>{resetError}</p>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button onClick={() => setShowResetModal(false)} className="btn btn-ghost" disabled={resetSubmitting}>Cancelar</button>
          <button onClick={confirmResetPassword} className="btn btn-primary" disabled={resetSubmitting || resetCode.length !== 6 || newPassword.length < 8}>
            {resetSubmitting ? 'Actualizando...' : 'Actualizar Contraseña'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
