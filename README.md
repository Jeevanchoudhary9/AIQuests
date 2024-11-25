# AIQuest: AI-Powered Knowledge-Sharing Platform

AIQuest is an advanced internal knowledge-sharing platform, inspired by Stack Overflow, designed to enhance collaboration and productivity within organizations. By integrating Retrieval-Augmented Generation (RAG) with the Llama AI model, the platform facilitates intelligent, contextual responses to user queries, combining AI insights with human expertise.

## Features

### Core Capabilities
- **Knowledge Sharing**: Employees can ask questions, provide answers, and leverage AI for automated responses.
- **AI-Generated Replies**: Contextual responses enhanced with confidence indicators and domain-specific optimizations.
- **Role-Based Access Control (RBAC)**: Secure access management for employees, moderators, and admins.
- **Question Similarity Checks**: AI-powered suggestions to avoid duplicate questions.
- **Feedback Mechanism**: Ratings for AI responses to improve future training cycles.

### Additional Enhancements
- **Gamification**: Leaderboards and rewards to encourage participation.
- **Notifications and Alerts**: Real-time updates for users and admins.
- **Security**: AES encryption and restricted access controls.

### AI Lifecycle Management
- **Monthly Model Training**: The Llama model is retrained every month using high-quality content from the RAG database.
- **Continuous Monitoring**: Performance metrics and user feedback integrated into Flask backend.

## Tech Stack

- **Backend Framework**: Flask
- **Database Systems**: PostgreSQL and Elasticsearch
- **AI Integration**: RAG-based model with Llama
- **APIs**: Flask-powered APIs for seamless interactions

## Architecture

1. **Backend**: Flask APIs manage queries, upvotes/downvotes, and AI responses.
2. **Database**: PostgreSQL for structured data and Elasticsearch for full-text search.
3. **AI Engine**: Llama, integrated with RAG for intelligent and contextual responses.
4. **Training Pipeline**:
   - Aggregate data from RAG.
   - Filter high-quality content based on user votes and admin validations.
   - Retrain the model monthly and replace the old database.

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
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 36 AM" src="https://github.com/user-attachments/assets/dfae6a3f-0018-431c-af0b-5627ae445f5d">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 07 AM" src="https://github.com/user-attachments/assets/a9c15233-3ecb-4670-8d41-a6e9697da48c">
<img width="1710" alt="Screenshot 2024-11-26 at 12 42 29 AM" src="https://github.com/user-attachments/assets/e4ee8777-b1f9-43b1-bf6f-64601e963791">
