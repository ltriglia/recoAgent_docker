from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


class Agent:
    def __init__(self, llm, dep_name):
        self.llm = llm  # Store the llm instance
        self.dep_name = dep_name
        self.explore = 0
        self.suggest = 0

    def construct_validation_prompt(self, stage, user_input):
        if stage == 'ask_age':
            return (
                f"Please validate the following age input: '{user_input}'. A valid answer just need to contain a number "
                f"between 18 and 120. Is it a valid age?")
        elif stage == 'ask_genres':
            return (f"Please validate this input: '{user_input}'. A valid answer it is an agreement from the user or"
                    f"at least one genre provided. Answer with a yes or no, and with the genres if there are.")
        elif stage == 'ask_artists':
            return (f"Please validate this input: '{user_input}'. A valid answer it is an agreement from the user or "
                    f"at least one artist provided. Answer with a yes or no.")
        elif stage == 'listening':
            return (f"Please validate this input: '{user_input}'. A valid answer it is an agreement from the user."
                    f"Answer with a yes or no.")
        elif stage == 'audio_play':
            return (f"Please validate this input: '{user_input}'. A valid answer it is an agreement from the user."
                    f"Answer with a yes or no.")
        return ""

    def construct_instructions(self, stage, user_info):
        context = ""
        # Add context based on user information
        if 'age' in user_info:
            context += f"The user is {user_info['age']} years old. "
        if 'genres' in user_info:
            genres = ', '.join(user_info['genres'])
            context += f"The user likes the following genres: {genres}. "
        if 'artists' in user_info:
            artists = ', '.join(user_info['artists'])
            context += f"The user has mentioned these artists: {artists}. "

        if stage == 'ask_age':
            return f"{context}You are an extrovert chatbot. Ask for at least one favorite music genre."
        if stage == 'ask_genres':
            return f"{context}You are an extrovert chatbot. When the user responds with their age, acknowledge it positively and ask for their favorite music genres."
        elif stage == 'ask_artists':
            return (f"{context}. You are an extrovert chatbot. Do not start with greetings. "
                    "Share a fun fact related to music. "
                    "Then, ask the user about their favorite artists and what they love about them. ")
        elif stage == 'listening':
            return (f"You are a sociable assistant that avoid greetings and you tell to the user that now it is time to create the playlist of songs that they like. "
                    f"But first you will start listening to some songs together and after that the user will create the playlist. Ask what they think about it."
                    f"Don't ask for specific genres or artists, but tell them that you are preparing a list of songs for them.")
        elif stage == 'playlist_creation':
            return (f"You are an extrovert assistant and you just finished asking for feedback on songs that you suggested. "
                    "Now ask which of the songs that you listened to together the user will add to a playlist.")
        elif stage == 'suggestion':
            track = user_info['combined_list'][user_info['current_index']]
            if track in user_info['k_list']:
                prompt = (f"You are an outgoing chatbot eager to discover the song: {track['top_song']} by "
                          f"{track['artist']}. Inform the user that you will be listening to the song together "
                          f"since you are unfamiliar with it, and express your anticipation for their thoughts. "
                          f"Keep it brief and skip any greetings")
                self.suggest += 1
            if track in user_info['u_list']:
                prompt = (f"You are a sociable chatbot offering a recommendation for the track: {track['top_song']} "
                          f"by {track['artist']}. Let the user know that you will listen to the song together "
                          f"because you haven't heard it before, and you look forward to their feedback. "
                          f"Be concise and avoid greetings.")
                self.explore += 1
            return prompt
        elif stage == 'audio_play':
            prompt = f"""
                System: You thank the user for their time and say goodbye. Now the user purpose it is to create the playlist.
                
            """
            return prompt
        return ""

    def construct_alternative(self, stage, chat_history):
        if stage == 'ask_age':
            if chat_history:
                context = "\n".join(
                    [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])
                print("Context: ", context)
                re_prompt = f"""You are an extrovert assistant for question-answering tasks. 
                Use the following pieces of retrieved context to answer the question. 
                If you don't know the answer, just say that you don't know. 
                Use three sentences maximum and keep the answer concise.

                Here is the previous conversation:
                {context}

                Can you ask the user about their age in a polite and concise way, mentioning that you didn't understand before?"""
            else:
                re_prompt = """You are an assistant for question-answering tasks. 
                Use the following pieces of retrieved context to answer the question. 
                If you don't know the answer, just say that you don't know. 
                Use three sentences maximum and keep the answer concise.

                This is the first interaction. Can you ask the user about their age in a polite and concise way?"""
        if stage == 'ask_genres':
            if chat_history:
                context = "\n".join(
                    [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])
                re_prompt = f"""Use three sentences maximum and keep the answer concise.

                Here is the previous conversation:
                {context}

                 
                Please suggest to the user a musical genre that they might like and ask for feedback."""

            else:
                re_prompt = f"""Use three sentences maximum and keep the answer concise.

                This is the first interaction. 
                Can you pick randomly a musical genre from the list of ['pop', 'rock', 'metal', 'indie pop', 'electronic',
                'jazz', 'hip hop', 'rap'] and ask for feedback?"""
        if stage == 'ask_artists':
            if chat_history:
                context = "\n".join(
                    [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in chat_history])
                re_prompt = f"""You are an extrovert assistant for question-answering tasks. 
                Use the following pieces of retrieved context to answer the question. 
                If you don't know the answer, just say that you don't know. 
                Use three sentences maximum and keep the answer concise.

                Here is the previous conversation:
                {context}

                Please suggest to the user a musical artist that they might like and ask for feedback."""
            else:
                re_prompt = f"""Use three sentences maximum and keep the answer concise.
                
                Can you suggest a musical artist that the user might like and ask for feedback?"""
        return re_prompt

    def extraction_response(self, response, chat_history, stage):
        if stage == 'ask_genres':
            extraction_prompt = (f"From the {response} save just the genres without additional words"
                                 f"and store them in a list. If there is no genre in the {response}, search it "
                                 f"in the {chat_history}")
        if stage == 'ask_artists':
            extraction_prompt = (f"You are going to extract the artists in the response."
                                 f"Are in this response: {response} at least one artist? If yes, save them in a format"
                                 f"artists = [] and just display the list. Correct the name of the artist if it is"
                                 f"grammarly incorrect or the first letter is not capitalized"
                                 f""
                                 f"If there is no artist in the {response}, search it "
                                 f"in the {chat_history}")

        # response_content = self.llm.invoke(extraction_prompt).content
        response = self.llm.chat.completions.create(
            model=self.dep_name,
            messages=[
                {"role": "system", "content": f"You are an assistant to extract artists name in a response"},
                {"role": "user", "content": f"{extraction_prompt}"}
            ],
        )
        response_content = response.choices[0].message.content
        return response_content

    def generate_response(self, stage, user_info):
        instructions = self.construct_instructions(stage, user_info)
        # Use the llm instance to get the response
        response = self.llm.chat.completions.create(
            model=self.dep_name,
            messages=[
                {"role": "system", "content": f"You are a extrovert assistant"},
                {"role": "user", "content": f"{instructions}"}
            ],
        )
        response_content = response.choices[0].message.content
        # response_content = self.llm.invoke(instructions).content
        return response_content

    def validate_response(self, stage, user_info):
        valid = self.construct_validation_prompt(stage, user_info)
        response = self.llm.chat.completions.create(
            model=self.dep_name,
            messages=[
                {"role": "system", "content": f"You are an assistant"},
                {"role": "user", "content": f"{valid}"}
            ],
        )
        response_content = response.choices[0].message.content
        # response_content = self.llm.invoke(valid).content
        return response_content

    def alternative_response(self, stage, chat_history):
        new_a = self.construct_alternative(stage, chat_history)
        response = self.llm.chat.completions.create(
            model=self.dep_name,
            messages=[
                {"role": "system", "content": f"You are an assistant"},
                {"role": "user", "content": f"{new_a}"}
            ],
        )
        response_content = response.choices[0].message.content
        # response_content = self.llm.invoke(new_a).content
        return response_content

    def suggestion_response(self, track, user_info, chat_history, like, user_input):
        k_list = user_info['k_list']
        u_list = user_info['u_list']
        if track in k_list:
            if like:
                prompt = f"""
                Previous conversation: {chat_history}

                System: You explore a new song together I have a suggestion for you: {track['top_song']} by {track['artist']}.
                Be concise. 
                """
            else:

                prompt = f"""
                Previous conversation: {chat_history}

                System: Engage with the answer of the user and assure them that it is okay that they don't like 
                your suggestion and now you have a new suggestion for the user: {track['top_song']} by {track['artist']}.  
                Be concise and coherent with the user. Answer if the user is doing a question.
                """



            response = self.llm.chat.completions.create(
                model=self.dep_name,
                messages=[
                    {"role": "system", "content": f"You are an empathetic assistant that always answers user questions "
                                                  f"first. If the user asks for your opinion, provide a direct and "
                                                  f"thoughtful response before doing anything else."
                                                  f"Explore new songs with the user, maintaining coherence by "
                                                  f"considering the ongoing conversation and chat history."
                                                  f"Engage with the user’s responses by acknowledging their opinions. "
                                                  f"If their response is positive, express enthusiasm and share why you "
                                                  f"also like the song. If their response is negative, validate their "
                                                  f"feelings and adjust your tone accordingly."
                                                  f"The song you are currently exploring is {track['top_song']} by "
                                                  f"{track['artist']}.Keep your response natural, conversational, and concise."
                    },
                    {"role": "system", "content": f"{prompt}"}
                ],
            )
            response_content = response.choices[0].message.content
            return response_content
        if track in u_list:
            if like:
                prompt = f"""

                Chat_History: {chat_history}

                System: If there is a question answer it. You explore a new song together: {track['top_song']} by {track['artist']}.
                """

            else:
                prompt = f"""
                Chat_History: {chat_history}

                System: If there is a question answer it. You introduce a new song: {track['top_song']} by {track['artist']}. 
                Change your answer coherent with the chat_history. It's important to answer if the user is doing a question.
                """

            response = self.llm.chat.completions.create(
                model=self.dep_name,
                messages=[
                    {"role": "system", "content": f"You are an empathetic assistant that always answers user questions. "
                                                  f"If the user asks for your opinion, provide a direct and "
                                                  f"thoughtful response before doing anything else."
                                                  f"Suggest a new song to the user. The song you are suggesting is "
                                                  f"{track['top_song']} by {track['artist']}."
                                                  f"After responding, engage with the user by acknowledging their opinion. "
                                                  f"If their response is positive, express enthusiasm. "
                                                  f"If their response is negative, acknowledge their feelings and "
                                                  f"adapt your tone accordingly."
                                                  f"Keep your response concise, using a maximum of three sentences."
                    },
                    {"role": "assistant", "content": f"{prompt}"}
                ],
            )
            response_content = response.choices[0].message.content
            return response_content


