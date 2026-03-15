export interface AuthUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
  tenantId: string;
}

export function getOidcConfig() {
  return {
    authority: process.env.NEXT_PUBLIC_OIDC_AUTHORITY || '',
    clientId: process.env.NEXT_PUBLIC_OIDC_CLIENT_ID || 'analyst-portal',
    redirectUri: process.env.NEXT_PUBLIC_OIDC_REDIRECT_URI || `${typeof window !== 'undefined' ? window.location.origin : ''}/auth/callback`,
    scope: 'openid profile email',
  };
}

export function parseToken(token: string): AuthUser | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.sub,
      email: payload.email,
      name: payload.name || payload.preferred_username,
      roles: payload.realm_access?.roles || [],
      tenantId: payload.tenant_id,
    };
  } catch {
    return null;
  }
}

export function hasRole(user: AuthUser, role: string): boolean {
  return user.roles.includes(role);
}

export function isLeadAnalyst(user: AuthUser): boolean {
  return hasRole(user, 'lead_analyst') || hasRole(user, 'admin');
}
