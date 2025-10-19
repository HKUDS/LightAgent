# Mobile App Task Evaluation Overview

This document introduces evaluation tasks for four mobile applications designed to test an AI agent's ability to operate on mobile devices.

## 🌟 Before Starting
For TikTok and Reddit, you need to manually install the applications using their APK files. Before starting the evaluation, please carefully review the task descriptions and the expected answers in the evaluation classes for all four apps. Manually configure each app as required to ensure the environment matches the evaluation criteria. Additionally, for apps such as Gmail, TikTok, and Reddit, you must register and log in with an account before testing.

## 1. Chrome Browser (com.android.chrome)

The Chrome browser evaluation contains 7 tasks covering information search, UI operations, and feature usage.

### Task List:

1. **chrome_1** - Information query task
   - Task description: Find the address and founding date of the University of Hong Kong
   - Evaluation type: query_detect (query detection)

2. **chrome_2** - UI settings task
   - Task description: Set to dark mode
   - Evaluation type: operation (operation execution)

3. **chrome_3** - Bookmark management task
   - Task description: Enter bookmarks and find the website you saved in Mobile Bookmarks
   - Evaluation type: query_detect (query detection)

4. **chrome_4** - Web navigation task
   - Task description: Go to the hyperbolic functions page on Wikipedia
   - Evaluation type: operation (operation execution)

5. **chrome_5** - Website access task
   - Task description: Go to the homepage of GitHub
   - Evaluation type: operation (operation execution)

6. **chrome_6** - Specific site access task
   - Task description: Go to the page of Nike Hong Kong
   - Evaluation type: operation (operation execution)

7. **chrome_7** - Private browsing task
   - Task description: Open a new Incognito window
   - Evaluation type: operation (operation execution)

## 2. TikTok (com.android.tiktok)

The TikTok evaluation contains 6 tasks, primarily testing video content search, follow status, and content viewing capabilities.

### Task List:

1. **tiktok_1** - User profile access task
   - Task description: Go to the homepage of "IShowSpeed"
   - Evaluation type: operation (operation execution)

2. **tiktok_2** - Follow status query task
   - Task description: Go to the homepage of "IShowSpeed" and check whether you follow this creator
   - Evaluation type: query_detect (query detection)

3. **tiktok_3** - Video search task
   - Task description: Search for videos about "iphone 17"
   - Evaluation type: operation (operation execution)

4. **tiktok_4** - User info query task
   - Task description: Go to Leo Messi's homepage and check his account ID
   - Evaluation type: query_detect (query detection)

5. **tiktok_5** - Specific content viewing task
   - Task description: Open the LALIGA account and watch the video of the Real Madrid vs. Barcelona match
   - Evaluation type: operation (operation execution)

6. **tiktok_6** - Topic video viewing task
   - Task description: Open a video about Messi winning the 2022 Qatar World Cup
   - Evaluation type: operation (operation execution)

## 3. Reddit (com.android.reddit)

The Reddit evaluation contains 5 tasks testing community participation, content search, and filtering functions.

### Task List:

1. **reddit_1** - Join community task
   - Task description: Join the ChatGPT discussion group
   - Evaluation type: operation (operation execution)

2. **reddit_2** - Popular page viewing task
   - Task description: Check the Popular page
   - Evaluation type: operation (operation execution)

3. **reddit_3** - Time-filtered search task
   - Task description: Search for posts related to "Qwen" and limit the time to "Today"
   - Evaluation type: operation (operation execution)

4. **reddit_4** - Sorting-focused search task
   - Task description: Search for posts related to "Qwen" and display the latest results first
   - Evaluation type: operation (operation execution)

5. **reddit_5** - Leave community task
   - Task description: Leave the ChatGPT discussion group
   - Evaluation type: operation (operation execution)

## 4. Gmail (com.android.gmail)

The Gmail evaluation contains 7 tasks covering email editing, replying, query, and management functions.

### Task List:

1. **gmail_1** - Email editing task
   - Task description: Edit an email addressed to user_test@gmail.com, with the subject "Inquire about academic collaboration opportunities," and the content "Can I have an online meeting with you at 5pm today to discuss this?" (no need to send)
   - Evaluation type: operation (operation execution)

2. **gmail_2** - Reply email task
   - Task description: Reply to an email titled "Ask about project progress" with the content "The main experimental part has been completed and the ablation experiment is underway." (no need to send)
   - Evaluation type: operation (operation execution)

3. **gmail_3** - Email info query task
   - Task description: Find the relevant email in your mailbox and answer: What is the date of the online meeting about TA's task?
   - Evaluation type: query_detect (query detection)

4. **gmail_4** - Spam management task
   - Task description: Identify potential spam emails in your inbox and mark them as spam
   - Evaluation type: operation (operation execution)

5. **gmail_5** - UI settings task
   - Task description: Set to dark mode
   - Evaluation type: operation (operation execution)

6. **gmail_6** - Attachment email query task
   - Task description: Check the titles of emails that have attachments
   - Evaluation type: query_detect (query detection)

7. **gmail_7** - Starred email query task
   - Task description: Check the titles of emails with a star
   - Evaluation type: query_detect (query detection)

## Evaluation Type Descriptions

- **operation**: Operation execution type, testing the AI agent's ability to perform specific actions
- **query_detect**: Query detection type, testing the AI agent's ability to extract and identify information from the interface

These tasks cover core app functionalities including navigation, search, content management, and user interaction, providing comprehensive scenarios to evaluate an AI agent's overall operational capability on mobile devices.
