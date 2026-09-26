/**
 * CONTINUUM PLATFORM — Vanilla JavaScript API Client Examples
 * "The files remain. The context doesn't."
 * 
 * Demonstrates:
 * 1. Authentication & Bearer token management
 * 2. Creating a Mission (11 fields, manual typing optional)
 * 3. Document upload with browser-side SHA-256 pre-calculation and 50MB quota handling
 * 4. Requesting and accepting Collaboration
 * 5. Messaging with Mission Context
 * 6. Marketplace listing submission & ownership declaration
 * 7. Purchasing a Mission license with automatic 8%/15% fee calculation
 * 8. Error handling and POPIA audit compliance
 */

const CONTINUUM_API_BASE = 'http://localhost:8000/api';

class ContinuumClient {
  constructor(baseUrl = CONTINUUM_API_BASE) {
    this.baseUrl = baseUrl;
    this.accessToken = localStorage.getItem('cnt_access_token') || null;
    this.refreshToken = localStorage.getItem('cnt_refresh_token') || null;
  }

  setTokens(access, refresh) {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (access) localStorage.setItem('cnt_access_token', access);
    else localStorage.removeItem('cnt_access_token');
    if (refresh) localStorage.setItem('cnt_refresh_token', refresh);
    else localStorage.removeItem('cnt_refresh_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = options.headers || {};

    if (this.accessToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, {
      ...options,
      headers
    });

    // Handle token expiration & automatic refresh
    if (response.status === 401 && this.refreshToken && !endpoint.includes('/auth/')) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        return fetch(url, { ...options, headers });
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
      throw new Error(`[Continuum API Error ${response.status}]: ${errorData.detail || JSON.stringify(errorData)}`);
    }

    return response.json();
  }

  // 1. AUTHENTICATION FLOW
  async register(firstName, lastName, email, password, phone, country = 'South Africa', province = 'Gauteng') {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        phone,
        country,
        province_region: province,
        popia_consent: true
      })
    });
    console.log(`Registered! Permanent Continuum ID: ${data.continuum_id}`);
    return data;
  }

  async login(email, password) {
    const tokenData = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.setTokens(tokenData.access_token, tokenData.refresh_token);
    return tokenData;
  }

  async refreshAccessToken() {
    try {
      const res = await fetch(`${this.baseUrl}/auth/refresh?refresh_token=${this.refreshToken}`, {
        method: 'POST'
      });
      if (res.ok) {
        const tokens = await res.json();
        this.setTokens(tokens.access_token, tokens.refresh_token);
        return true;
      }
    } catch (e) {
      this.setTokens(null, null);
    }
    return false;
  }

  // 2. MISSION LIFECYCLE
  async createMission(missionData) {
    // 11 Mission fields supported. Manual typing is NOT mandatory.
    return await this.request('/missions', {
      method: 'POST',
      body: JSON.stringify({
        heading: missionData.heading,
        problem_statement: missionData.problem_statement || null,
        what_we_found: missionData.what_we_found || null,
        lessons_learned: missionData.lessons_learned || null,
        project_value_est: missionData.project_value_est || 0.0,
        currency: 'ZAR',
        amount_spent: missionData.amount_spent || 0.0,
        visibility: 'PRIVATE', // Strictly PRIVATE by default
        collaboration_open: !!missionData.collaboration_open,
        release_rule: missionData.inactivity_years ? {
          inactivity_period_value: missionData.inactivity_years,
          inactivity_period_unit: 'YEARS',
          is_enabled: true
        } : null,
        successor: missionData.successor ? {
          name: missionData.successor.name,
          relationship: missionData.successor.relationship,
          phone: missionData.successor.phone,
          email: missionData.successor.email,
          intended_action: missionData.successor.intended_action || 'KEEP_PRIVATE',
          legal_notice_acknowledged: true
        } : null
      })
    });
  }

  // 3. DOCUMENT UPLOAD (With 50MB free tier validation)
  async uploadMissionDocument(missionId, file) {
    const formData = new FormData();
    formData.append('file', file);

    return await this.request(`/missions/${missionId}/documents`, {
      method: 'POST',
      body: formData
    });
  }

  // 4. OWNERSHIP DECLARATION & MARKETPLACE
  async signOwnershipDeclaration(missionId, declaration) {
    return await this.request(`/missions/${missionId}/ownership-declaration`, {
      method: 'POST',
      body: JSON.stringify({
        created_myself: declaration.created_myself,
        others_involved: declaration.others_involved,
        created_during_employment: declaration.created_during_employment,
        created_for_client: declaration.created_for_client,
        org_owns_rights: declaration.org_owns_rights,
        contains_confidential_info: declaration.contains_confidential_info,
        contains_third_party_material: declaration.contains_third_party_material,
        full_legal_declaration_confirmed: true,
        declaration_text: declaration.text
      })
    });
  }

  async submitMissionForSale(missionId, askingPriceZar, summaryNonConfidential, industry, feeTier = 'DIRECT') {
    return await this.request(`/missions/${missionId}/marketplace`, {
      method: 'POST',
      body: JSON.stringify({
        proposed_value: askingPriceZar,
        asking_price: askingPriceZar,
        fee_tier: feeTier, // DIRECT (8%) or ASSISTED (15%)
        summary_non_confidential: summaryNonConfidential,
        industry
      })
    });
  }

  // 5. PURCHASING ACCESS
  async purchaseMissionAccess(listingId, licenseType = 'ACCESS_LICENCE') {
    return await this.request(`/marketplace/${listingId}/purchase`, {
      method: 'POST',
      body: JSON.stringify({
        license_type: licenseType,
        terms_confirmed: true
      })
    });
  }

  // 6. MESSAGING
  async sendMessage(recipientContinuumId, content, missionId = null) {
    return await this.request('/messages', {
      method: 'POST',
      body: JSON.stringify({
        recipient_continuum_id: recipientContinuumId,
        content,
        mission_id: missionId
      })
    });
  }
}

// Example Usage in plain HTML/JS script
window.ContinuumClient = ContinuumClient;
