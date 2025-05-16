import { defineStore } from 'pinia'
import axios from 'axios'
import Cookies from 'js-cookie';


export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as { id: number; last_name: string; first_name: string; role: string; login: string } | null
  }),
  actions: {
    async fetchCurrentUser() {
      const access_token = Cookies.get('access_token');
      const { data } = await axios.get('/api/users/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      this.user = data.User
    },
    clearUser: function () {
      this.user = null;
      Cookies.remove('access_token');
    },
  }
})