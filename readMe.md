## Introduction
Inside this folder you will find two streamlit applications to test the influence on a user regarding musical recommendations in
two scenarios. 
1. The Form folder contains the application to test the form interface
2. The Chat folder contains the application to the the chat interaface

### How to run the code
To run the code install the requirements with 
```
pip install -r requirements.txt
```

then depending on which application you want to run you have two options
```
streamlit run Chat/Introduction.py
```

```
streamlit run Form/Introduction.py
```
### Requirements
To run the code you need a **openai key** and a **spotify application code**. 

### Note
If you want you can also deploy the application on Docker. Inside each of the folder you will find a Dockerfile for the creation
of the container