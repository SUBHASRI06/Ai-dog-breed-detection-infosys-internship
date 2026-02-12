🐶 AI-Powered Dog Breed Detection & Information Generation

Infosys Springboard Virtual Internship 6.0 Project

📌 Overview

This project was developed as part of the Infosys Springboard Virtual Internship 6.0 (8 Weeks).

It is an end-to-end AI web application that:

Classifies dog breeds from uploaded images using Deep Learning

Generates detailed breed information using Generative AI

Provides secure user authentication and profile management

Stores user prediction history

The system integrates Computer Vision, Transfer Learning, Generative AI, and Web Application Development into a production-ready solution.

🎯 Objectives

Develop a high-accuracy CNN model for multi-class dog breed classification

Enhance user experience by automatically generating breed-specific descriptions

Build a scalable AI-powered web application for real-world use cases

🧠 Model Architecture

Dataset: Public dataset containing 120+ dog breeds

Base Model: Xception (Transfer Learning)

Framework: TensorFlow & Keras

Training Strategy:

80-20 Train-Validation Split

Data Augmentation (Rotation, Flip, Zoom, Brightness)

Dropout Regularization

Early Stopping

Adam Optimizer with Categorical Crossentropy Loss

The model is optimized for robust multi-class classification while minimizing overfitting.

🌐 Application Features

Image upload and real-time breed prediction

AI-generated detailed breed information (via Gemini API integration)

Secure user authentication system

User profile management

Detection history stored using SQLite

Interactive and responsive UI built with Streamlit

🛠️ Technology Stack
Category	Technologies Used
Programming	Python
Deep Learning	TensorFlow, Keras
Model Architecture	Xception
Image Processing	OpenCV, NumPy
Data Handling	Pandas, SQLite
Web Framework	Streamlit
Generative AI	Google Gemini API
Evaluation	Scikit-learn
Visualization	Matplotlib, Seaborn
🏗️ Project Workflow

Data Collection & Exploration

Data Preprocessing & Augmentation

Model Development using Transfer Learning

Streamlit-Based Web Application Development

Integration of Generative AI for Breed Information

Testing, Optimization & Performance Tuning

Documentation & Final Deployment

🚀 Installation & Execution
1️⃣ Clone the Repository
git clone https://github.com/SUBHASRI06/Ai-dog-breed-detection-infosys-internship.git
cd Ai-dog-breed-detection-infosys-internship

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Run the Application
streamlit run app.py

⚙️ Key Challenges & Solutions

Class Imbalance: Addressed using data augmentation techniques

Overfitting: Controlled through dropout and early stopping

Inference Latency: Optimized preprocessing pipeline

API Rate Limiting: Implemented caching strategies

Environment Consistency: Standardized dependencies

📈 Key Learnings

Advanced understanding of Convolutional Neural Networks and Transfer Learning

Full-stack AI application development

Secure authentication and database integration

Generative AI integration in production systems

End-to-end AI deployment workflow

🎓 Internship Details

Program: Infosys Springboard Virtual Internship 6.0

Duration: 8 Weeks

Role: Individual Project Developer

Project Title: AI Model for Dog Breed Detection and Information Generation

👩‍💻 Developer

Subhasri N M
Engineering Student | AI & Machine Learning Enthusiast

📌 Conclusion

This project demonstrates the practical implementation of deep learning and generative AI in a real-world application setting. It reflects hands-on experience in model development, system integration, UI design, and deployment within a structured internship framework.

⭐ If you find this project interesting, feel free to explore and provide feedback.