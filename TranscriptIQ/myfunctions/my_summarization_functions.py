from transformers import pipeline
import nltk
from nltk import ne_chunk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from pyecharts import options as opts
from pyecharts.charts import Graph
from pyecharts.globals import ThemeType
import emoji
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# Initialize summarizer with a smaller model
try:
    # Using a smaller model that's more memory efficient
    summarizer = pipeline("summarization", model="t5-small")
except Exception as e:
    print(f"Error loading summarizer: {str(e)}")
    summarizer = None

def summarize_with_huggingface(text, max_length=150, min_length=50):
    """Summarizes the given text using Hugging Face transformers.
    
    For longer texts, splits into chunks and summarizes each chunk separately.
    """
    if not text.strip():
        return "No content available for summarization."
    
    if summarizer is None:
        return "Summarization model not available. Please try again later."
    
    # Maximum token length for the model (approximately 512 tokens)
    MAX_CHUNK_LENGTH = 2000  # characters
    
    # If text is short enough, summarize directly
    if len(text) <= MAX_CHUNK_LENGTH:
        try:
            summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            return f"Error during summarization: {str(e)}"
    
    # For longer texts, split into chunks and summarize each chunk
    try:
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= MAX_CHUNK_LENGTH:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Summarize each chunk
        summaries = []
        for chunk in chunks:
            try:
                summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            except Exception as e:
                print(f"Error summarizing chunk: {str(e)}")
                continue
        
        # Combine summaries
        if summaries:
            return " ".join(summaries)
        else:
            return "Unable to generate summary due to errors."
    except Exception as e:
        return f"Error during chunked summarization: {str(e)}"

def get_bullet_points(text, query, api_key):
    """Generates bullet points or specific summary based on user query."""
    # Initialize the ChatOpenAI model
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", openai_api_key=api_key)
    
    # Create a prompt template for bullet points
    bullet_prompt = PromptTemplate(
        input_variables=["text", "query"],
        template="""Given the following text and query, provide a detailed response in bullet points format.
        Focus on the specific aspects mentioned in the query.
        
        Text: {text}
        
        Query: {query}
        
        Please provide the response in the following format:
        • Main point 1
          - Supporting detail 1.1
          - Supporting detail 1.2
        • Main point 2
          - Supporting detail 2.1
          - Supporting detail 2.2
        
        Response:"""
    )
    
    # Format the prompt with the text and query
    formatted_prompt = bullet_prompt.format(text=text, query=query)
    
    # Get the response from the model
    response = llm.predict(formatted_prompt)
    
    return response

# ✅ Alias function for backward compatibility
summarize_with_cohere = summarize_with_huggingface

def ner_nltk(text):
    """Performs Named Entity Recognition (NER) using NLTK."""
    # Tokenize and POS tag the text
    tokens = word_tokenize(text)
    pos_tags = pos_tag(tokens)
    
    # Perform NER
    named_entities = ne_chunk(pos_tags)
    
    # Extract entities
    entities = []
    for entity in named_entities:
        if hasattr(entity, 'label'):
            entities.append((entity[0][0], entity.label()))
    
    return entities

def filter_special_chars(text):
    """Removes special characters and emojis from the text."""
    return emoji.demojize(text)

def get_graph(transcription_text, save_path, DEBUG=False):
    """Generates a Named Entity Recognition (NER) graph with pyecharts."""
    data = {}
    transcription_text = filter_special_chars(transcription_text)
    
    # Get entities using NLTK
    entities = ner_nltk(transcription_text)
    
    # Group entities by type
    for entity, label in entities:
        if label not in data:
            data[label] = [entity]
        else:
            data[label].append(entity)

    category_list = list(data.keys())
    categories = [opts.GraphCategory(name=n) for n in category_list]

    nodes = []
    for key, values in data.items():
        values = list(set(values))  # Remove duplicates
        for value in values[:10]:  # Limit nodes per category
            nodes.append(
                opts.GraphNode(
                    name=value,
                    category=key,
                    symbol_size=10
                )
            )

    # Create links between nodes of the same category
    links = []
    for i, node1 in enumerate(nodes):
        for node2 in nodes[i+1:]:
            if node1.category == node2.category:
                links.append(
                    opts.GraphLink(
                        source=node1.name,
                        target=node2.name,
                        value=1
                    )
                )

    # Create the graph
    graph = (
        Graph(init_opts=opts.InitOpts(theme=ThemeType.DARK))
        .add(
            "",
            nodes,
            links,
            categories,
            repulsion=8000,
            is_draggable=True,
            layout="force",
            edge_length=100,
            is_roam=True,
            edge_symbol=['circle', 'arrow'],
            edge_symbol_size=6,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Named Entity Recognition Graph"),
            legend_opts=opts.LegendOpts(is_show=True),
        )
    )

    # Save the graph
    graph.render(save_path)
    return graph

# ✅ Test the summarization function (Run this file directly)
if __name__ == "__main__":
    test_text = """
    Google is introducing AI-powered features in search and Gmail, making it easier for users to find 
    information and compose emails more efficiently. The new AI search will provide more interactive 
    results with a conversational mode.
    """
    
    summary = summarize_with_huggingface(test_text)
    print("🔹 Original Text:\n", test_text)
    print("\n🔹 Summarized Text:\n", summary)
