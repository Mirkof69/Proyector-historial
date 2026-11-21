export type LoginStep = 'credentials' | 'totp' | 'setup_required';

export interface CredentialsForm {
  email: string;
  password: string;
  remember?: boolean;
}

export interface TotpForm {
  totp_code: string;
}

export interface LocationState {
  from?: string;
}
