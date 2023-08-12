import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css';



const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [botResponse, setBotResponse] = useState({});
  const [excelResponse, setExcelResponse] = useState('');

  const handleValueChange = (section, key, newValue) => {
    setBotResponse((prevResponse) => ({
      ...prevResponse,
      [section]: {
        ...prevResponse[section],
        [key]: newValue,
      },
    }));
  };

  const handleExportToExcelClick = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/exportToExcel', {
        responseType: 'blob',
        headers: {
          Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }, // Set the response type to blob (binary data)
      });


      // Create a blob URL for the Excel file
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const blobUrl = URL.createObjectURL(blob);
  
      //Create a download link and trigger a click event to download the file
      const downloadLink = document.createElement('a');
      downloadLink.href = blobUrl;
      downloadLink.download = 'generated_excel.xlsx';
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
    } catch (error) {
      console.error('Error exporting Excel file:', error);
    }
  };
  
  const convertValuesToFloat = (obj) => {
    const convertedObj = {};
    
    for (const key in obj) {
      if (typeof obj[key] === 'object') {
        convertedObj[key] = convertValuesToFloat(obj[key]);
      } else if (!isNaN(parseFloat(obj[key]))) {
        convertedObj[key] = parseFloat(obj[key]);
      } else {
        convertedObj[key] = obj[key];
      }
    }
    
    return convertedObj;
  };

  const formatBotResponse = (response) => {
    // Convert the dictionary object to an array of [key, value] pairs
    const keyValuePairs = Object.entries(response);
  
    // Create a <div> element for each key-value pair
    return keyValuePairs.map(([key, value], index) => (
      <div key={index}>
        {`| ${key} | ${value} |`}
      </div>
    ));
  };

  const sendMessage = async () => {
    if (inputValue.trim() === '') return;

    const newMessage = { text: inputValue, fromUser: true };
    setMessages([...messages, newMessage]);
    setInputValue('');

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/chatbot', {
        message: inputValue,
      });
      setBotResponse(JSON.parse(response.data.message));
      setExcelResponse(JSON.parse(response.data.excel));
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      const convertedEntryAss = convertValuesToFloat(botResponse.entry_ass);
      const convertedIsAss = convertValuesToFloat(botResponse.is_ass);
      const response = await axios.post('http://127.0.0.1:5000/api/submit', {
        entry_ass: convertedEntryAss,
        is_ass: convertedIsAss,
      });

      const botMessage = { text: formatBotResponse(response.data.message), fromUser: false };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error('Error submitting data:', error);
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
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
      <div className="bot-response-table">
        <h3>Entry Assumptions:</h3>
        {Object.keys(botResponse.entry_ass || {}).length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(botResponse.entry_ass || {}).map(([key, value], index) => (
                <tr key={index}>
                  <td>{key}</td>
                  <td>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => handleValueChange('entry_ass', key, e.target.value)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No entry assumptions from the bot yet.</p>
        )}
      </div>
      <div className="bot-response-table">
        <h3>Interest Assumptions:</h3>
        {Object.keys(botResponse.is_ass || {}).length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(botResponse.is_ass || {}).map(([key, value], index) => (
                <tr key={index}>
                  <td>{key}</td>
                  <td>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => handleValueChange('is_ass', key, e.target.value)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No interest assumptions from the bot yet.</p>
        )}
      </div>
      <div className="bot-response-table">
      <h3>Excel Table Output</h3>
      <span>{excelResponse}</span>
    </div>
      <div className="submit-button">
        <button onClick={handleSubmit}>Submit</button>
      </div>

      <div className="export-button">
      <button onClick={handleExportToExcelClick}>Export to Excel</button>
    </div>

    </div>
    
    
  );
};

export default Chatbot;
