import axios from 'axios';

const API = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    timeout: 8000,
});

// chat
export const SendMessage = async (text) => {
    const response = await API.post('/chat/message',{
        message : text
    });
    return response.data;
};


// restaurantes

export const getRestaurants = async() => {
    const response = await API.get("/restaurants");
    return response.data;
}

// status
export const getStatus = async() => {
    return API.get("/status");
};

export default API;