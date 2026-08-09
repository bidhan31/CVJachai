const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://cvjachai.online/api';

export const authApi = {
  signin: async (email, password) => {
    const response = await fetch(`${BASE_URL}/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    return response.json();
  },

  signup: async (firstName, lastName, email, password) => {
    const response = await fetch(`${BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ 
        first_name: firstName, 
        last_name: lastName, 
        email, 
        password 
      }),
    });
    return response.json();
  },
  
  requestOtp: async (email) => {
    const response = await fetch(`${BASE_URL}/auth/otp/request/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    return response.json();
  },

  resetPassword: async (email, otpCode, newPassword) => {
    const response = await fetch(`${BASE_URL}/auth/reset-password/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ 
        email, 
        otp_code: otpCode, 
        new_password: newPassword 
      }),
    });
    return response.json();
  },

  googleLogin: async (token) => {
    const response = await fetch(`${BASE_URL}/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ token }),
    });
    return response.json();
  },
};

export const resumeApi = {
  classify: async (formData, token) => {
    // formData contains: job_circular, resume_files (file), top_k, skills, min_experience
    const response = await fetch(`${BASE_URL}/classify`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData,
    });
    return response.json();
  },

  optimize: async (formData, token) => {
    // formData contains: resume_file (file), job_description (text, optional)
    const response = await fetch(`${BASE_URL}/optimize`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData,
    });
    return response.json();
  },
};

export const jobApi = {
  getJobs: () => {
    return fetch(`${BASE_URL}/jobs/`, {
      method: "GET",
      headers: { "Accept": "application/json" },
      redirect: "follow"
    });
  },

  getMyJobs: (token) => {
    return fetch(`${BASE_URL}/jobs/my/`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}`, "Accept": "application/json" }
    });
  },

  createJob: (payload, token) => {
    return fetch(`${BASE_URL}/jobs/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(payload),
      redirect: "follow"
    });
  },

  deleteJob: (id, token) => {
    return fetch(`${BASE_URL}/jobs/${id}/delete/`, {
      method: "DELETE",
      headers: { 
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
        "Accept": "application/json"
      }
    });
  },

  getApplicants: (jobId, token) => {
    return fetch(`${BASE_URL}/jobs/${jobId}/applications/`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}`, "Accept": "application/json" }
    });
  },

  analyzeApplicants: (jobId, formData, token) => {
    return fetch(`${BASE_URL}/jobs/${jobId}/analyze/`, {
      method: "POST",
      headers: { 
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json"
      },
      body: formData
    });
  },

  applyForJob: (formData) => {
    return fetch(`${BASE_URL}/jobs/apply/`, {
      method: "POST",
      body: formData,
      redirect: "follow"
    });
  }
};
