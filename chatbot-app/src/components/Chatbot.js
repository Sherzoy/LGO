import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');

  const formatBotResponse = (response) => {
    // Split the response text by newlines
    const lines = response.split('\n');
    // Create a <div> element for each line
    return lines.map((line, index) => <div key={index}>{line}</div>);
  };

  const sendMessage = async () => {
    if (inputValue.trim() === '') return;

    // Add the user message to the state
    const newMessage = { text: inputValue, fromUser: true };
    setMessages([...messages, newMessage]);
    setInputValue('');

    // Make the API call to the Flask server
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/chatbot', {
        message: inputValue
      });

      // Format the bot's response before setting it in the state
      const formattedResponse = formatBotResponse(response.data.message);
      const botMessage = { text: formattedResponse, fromUser: false };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-messages">
        {messages.map((message, index) => (
          <div key={index} className={message.fromUser ? 'user-message' : 'bot-message'}>
            {message.text}
          </div>
        ))}
      </div>
      <div className="chatbot-input">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              sendMessage();
            }
          }}
          placeholder="Paste code..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chatbot;
