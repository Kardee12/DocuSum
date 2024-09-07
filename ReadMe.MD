# Docusum

Docusum is an innovative platform designed to bridge the gap between research and education for the masses. It leverages large language models (LLMs) to perform actions like question-answering, summarization, translation, editing, and more. By allowing users to interact with complex documents using cutting-edge AI models, Docusum makes research more accessible and understandable. The platform is modular, enabling users to choose from a variety of LLMs, including their own custom models, cloud-based models, or those provided by services like OpenAI.

## How Docusum Empowers Education and Students

Docusum is tailored to help students and educators alike by simplifying the way they engage with research and educational materials. For students, especially those navigating complex academic papers or large volumes of research content, Docusum provides tools to break down dense information into digestible formats. The platform enables students to:

- **Quickly Summarize Research**: With Docusum’s summarization feature, students can automatically condense lengthy research papers or textbooks into concise overviews, making it easier to grasp the core ideas without getting overwhelmed by details.
  
- **Interactive Learning**: Docusum’s question-answering feature allows students to ask specific questions related to their study materials. By receiving instant, accurate answers directly from the text, students can focus on learning and understanding the material in real time.

- **Accessible Learning for All**: With text-to-speech functionality, Docusum can help students who prefer or need to consume content audibly. This makes learning more accessible to students with visual impairments or those who learn better through listening rather than reading.

- **Visual and Video Learning**: The text-to-image feature can assist visual learners by transforming text descriptions into corresponding images, helping students better visualize abstract concepts. Additionally, we are working on implementing **text-to-video** functionality, which will allow users to generate videos based on textual descriptions, adding another layer of interactive learning.

For educators, Docusum is a tool that can make lesson preparation faster and more effective. Teachers can use the platform to summarize materials for their students, create visual and video aids from textual content, and quickly extract answers for frequently asked questions. Docusum allows for flexible interaction with documents, enhancing both teaching and learning experiences in educational settings.

## Key Features

- **Document Summarization**: Automatically generate concise summaries of large documents.
- **Question Answering**: Ask questions about specific documents and receive accurate answers directly from the content.
- **Text-to-Image**: Transform textual descriptions into corresponding images, adding visual context to the analysis.
- **Text-to-Speech**: Convert document content into speech to improve accessibility and offer an alternative way to consume the information.
- **Text-to-Video**: In development. Generate videos based on textual descriptions to support more interactive learning.
- **Modular LLM Integration**: Users can choose from a range of pre-built models or integrate their own custom-trained LLMs for document processing.

## Technology Stack

Docusum is built on a modern tech stack designed for scalability, flexibility, and performance. The following technologies are used in the development and deployment of the platform:

- **Django**: Django is the primary web framework used to develop the platform's backend. It is known for its clean, pragmatic design and is used to manage user authentication, document uploading, and LLM model integrations.
  
- **Docker**: Docusum uses Docker to containerize the application and its dependencies, allowing for easy deployment across different environments. Docker Compose is employed to orchestrate multiple services, including the database and caching systems.
  
- **PostgreSQL**: PostgreSQL is the relational database management system (RDBMS) powering Docusum's database. It stores user data, uploaded documents, and logs, ensuring data is secure and easily accessible.
  
- **Redis**: Redis is used to manage chat history on the platform, ensuring users can easily retrieve and continue previous interactions with the system. It also helps with efficient task queuing to improve the platform’s performance when processing large-scale data.

- **LangChain**: Docusum leverages LangChain for building and managing LLM-powered applications. LangChain provides tools to facilitate prompt engineering, document parsing, and LLM integration, streamlining the workflow for developers.

## Future Vision

While Docusum already offers a wide array of features, we envision it becoming an even more powerful and transformative tool in the world of education and research. Our ideal future goals for Docusum include:

1. **Real-Time Document Collaboration**  
   We aim to add real-time collaboration features that allow multiple users to simultaneously interact with and edit documents, powered by LLMs. This would enable group learning, co-authoring research papers, and interactive tutoring, where LLMs can guide discussions or provide feedback in real time.

2. **Adaptive Learning and Research Recommendations**  
   Docusum could evolve into an adaptive learning platform, where it not only answers questions but also identifies gaps in students' knowledge and recommends tailored research materials, exercises, or resources based on their interactions with the platform.

3. **Multimodal Learning Experiences**  
   Beyond text-to-video, we aim to integrate more advanced multimodal learning experiences, combining audio, video, and interactive diagrams. By leveraging AI, we want to turn static documents into dynamic, engaging learning tools that adapt to each user’s needs.

4. **Seamless Integration with Popular Educational Platforms**  
   We envision Docusum seamlessly integrating with popular educational tools like Canvas. This would allow educators and students to incorporate Docusum’s features directly into their existing workflows, making it even more useful and accessible.

5. **AI-Powered Research Insights**  
   In the future, Docusum could be enhanced to provide deeper insights, like automatically generating hypotheses from research papers or identifying potential errors and contradictions in documents. This could drastically accelerate the research process, empowering both novice and experienced researchers.

6. **Open-Source Community and Model Sharing**  
   We aim to foster an open-source community around Docusum, where users can share and collaborate on custom LLM models, document workflows, and educational tools. This would create a thriving ecosystem where students, educators, and researchers can continuously improve the platform.


## Roadmap & TODOs

The platform is under continuous development with exciting new features and improvements in the pipeline. Here are the key tasks on the roadmap:

1. **Redo Site UI**  
   A complete overhaul of the user interface is planned to improve the overall user experience. The new UI will focus on ease of use, making it intuitive for users to upload documents, select AI models, and access the platform’s features.

2. **Integrate Code Additions**  
   Newly developed features, bug fixes, and performance improvements will be integrated into the platform. This includes optimizations to the document-processing engine and additions to the existing LLM workflows.

3. **Allow for Users to Use Custom Models**  
   One of the core future goals is to allow users to upload and use their custom-trained models. By providing the flexibility to work with different LLMs, this feature will enable users to tailor the document analysis to their specific needs.

4. **Use Cloud Models**  
   Integration with cloud-based LLM services is in progress. This will allow users to tap into state-of-the-art models hosted on platforms like AWS, Google Cloud, and others, ensuring the platform scales with user needs.

## How to Contribute
 Here’s how you can get involved:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or further information, feel free to reach out via karthik.manishankar@sjsu.edu
 - Additional Contacts will be added shortly