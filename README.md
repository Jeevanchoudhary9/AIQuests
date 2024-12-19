# AIQuest

**AIQuest** is an advanced internal knowledge-sharing platform, inspired by Stack Overflow, designed to revolutionize collaboration and productivity within organizations. Leveraging **Retrieval-Augmented Generation (RAG)** with the **Llama AI model**, AIQuest facilitates intelligent, contextual responses to user queries by combining the power of AI with human expertise.

---

## Core Capabilities

### **Knowledge Sharing**
- Employees can ask questions, provide answers, and utilize AI-generated responses.

### **AI-Generated Replies**
- Contextual responses are derived from:
  - **Company documents** stored in a hybrid RAG.
  - **Previously asked questions** and official answers stored in a simple RAG.
  - **Wikipedia**, when internal sources lack relevant information.

### **Role-Based Access Control (RBAC)**
- Provides secure and hierarchical access for employees, moderators, and admins.

### **Voting Mechanism**
- Users can like questions and upvote or downvote answers, influencing search ranking and visibility.

### **Search Facility**
- Allows users to search questions based on keywords or context.

### **Filtering**
- Filters questions by ranking (likes) or most recent.

### **Official Answers**
- Moderators can:
  - Mark an answer as official.
  - Provide official answers stored in the simple RAG for AI use.

### **Organizational Features**
- Organizations can:
  - Register and invite employees via email, including invite codes.
  - Gain insights through a dashboard:
    - **Metrics**: Total users, questions, answers, registered users, and invited users.
    - **Recent questions and uploaded documents.**
    - **Activity graph** (questions/answers vs. date).
    - **Visualization of top 5 tags.**
  - Upload company documents to the hybrid RAG.
  - Review and delete inappropriate questions.

### **Moderation of Responses**
- Moderation API checks for abusive or toxic content in both user-generated and AI responses.

### **Moderator Features**
- Moderators can:
  - Post questions, give official answers, or mark answers as official.
  - View metrics such as total users, questions, and answers.
  - Moderate questions (e.g., delete inappropriate ones, mark answers as official).
  - Visualize moderation status through a pie chart.

### **User Features**
- Users can:
  - Post questions (moderated for toxicity) and receive AI-generated answers.
  - Answer questions, like questions, and upvote or downvote answers.

---

## Tech Stack

- **Backend Framework:** Flask  
- **Database Systems:** SQLite for structured data, PostgreSQL for dashboard data.  
- **RAG Database:** Elasticsearch for hybrid and simple RAG.  
- **AI Integration:** Llama3.2 (locally using Ollama).  
- **APIs:** Flask-powered APIs for seamless interactions.  
- **AI Orchestration:** LangChain and PyTorch.  
- **Libraries:** PyPDF2 for document parsing and chunking.  
- **Search Ranking:** BM25 (sparse vectors) and all-MiniLM-L6-v2 embeddings (dense vectors).

---

## Architecture and Workflow

### **Hybrid RAG**
- **Documents** are parsed, chunked, and stored using:
  - **Sparse vectors** for syntactic search (BM25 ranking).
  - **Dense vectors** for semantic search (all-MiniLM-L6-v2 embeddings).
- Combined results from syntactic and semantic searches are ranked using **Reciprocal Rank Fusion (RRF)** for optimal output.

### **Simple RAG**
- Stores embeddings of **questions** and their **official answers**.

### **Organizational Workflow**
1. **Document Uploads**:
   - Parsed and read via PyPDF2.
   - Stored as dense vectors in the hybrid RAG (BM25 supports syntactic search natively in Elasticsearch).
2. **Dashboard Insights**:
   - Metrics, graphs, and visualizations (e.g., activity trends and top tags).

### **Moderator Workflow**
- Marking or providing official answers:
  - Embedded and stored in the simple RAG.

### **User Workflow**
1. **Posting Questions**:
   - Questions are checked for toxicity using the Moderation API.
   - Stored in SQLite.
   - Processed by the hybrid RAG to retrieve relevant documents (syntactic and semantic search).  
   - If no results are found, Wikipedia is queried for context.
2. **Answer Generation**:
   - Llama3.2 generates contextual responses based on retrieved documents or Wikipedia context.
   - Responses are moderated for toxicity and stored in the database.

### **AI Training Pipeline**
1. Aggregates data from the RAG.
2. Filters high-quality content based on user votes and admin validations.
3. Retrains the Llama3.2 model monthly and updates the RAG database.

---

## Key Features of RAG

### **Hybrid RAG (Documents)**
- Supports both syntactic (BM25) and semantic (dense vector) search.
- Efficiently retrieves and ranks documents for AI response generation.

### **Simple RAG (Questions & Official Answers)**
- Stores embeddings of user questions and moderator-verified official answers.
- Enables accurate contextual retrieval during AI response generation.

---

## How to Use

1. Clone the repository:
   ```bash
   git clone https://github.com/Jeevanchoudhary9/AIQuests.git
   ```
2. Navigate to the project directory and install dependencies:
   ```bash
   cd AIQuests
   pip install -r requirements.txt
   ```
3. Configure your environment variables for Flask, PostgreSQL, and Elasticsearch.
4. Run the application:
   ```bash
   flask run
   ```
5. Access the platform at `http://localhost:5000`.

## Future Improvements

- Enhanced gamification features.
- Integration with additional organizational tools.
- Advanced analytics for AI performance.

<img width="1710" alt="Screenshot 2024-11-26 at 12 42 13 AM" src="https://github.com/user-attachments/assets/a35674a3-09eb-43e2-bdca-ebb13b95bb35">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 16 AM" src="https://github.com/user-attachments/assets/3a91a07e-233c-4438-a462-0d85e48c852e">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 01 AM" src="https://github.com/user-attachments/assets/2b224c9c-49be-434c-8998-1b9abe9ceed8">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 07 AM" src="https://github.com/user-attachments/assets/a9c15233-3ecb-4670-8d41-a6e9697da48c">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 29 AM" src="https://github.com/user-attachments/assets/e4ee8777-b1f9-43b1-bf6f-64601e963791">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 36 AM" src="https://github.com/user-attachments/assets/dfae6a3f-0018-431c-af0b-5627ae445f5d">
