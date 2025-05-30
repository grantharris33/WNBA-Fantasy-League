export interface UserCreate {
  email: string;
  password: string;
}

export interface UserOut {
  id: number;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}