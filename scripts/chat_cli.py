from dotenv import load_dotenv

from nucleai.agent.core import create_nucleai_agent

# Load environment variables
load_dotenv()


def main():
    """Simple CLI for testing the NucleAI agent."""
    try:
        agent = create_nucleai_agent()
        print("NucleAI Chat CLI (Type 'exit' to quit)")
        print("-" * 40)

        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    break

                if not user_input.strip():
                    continue

                print("Agent is thinking...")
                # Invoke the agent with messages format
                response = agent.invoke({"messages": [("user", user_input)]})

                # Extract the last message content
                if "messages" in response and response["messages"]:
                    last_message = response["messages"][-1]
                    print(f"Agent: {last_message.content}")
                else:
                    print("Agent: (No response)")

                print("-" * 40)
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"Failed to initialize agent: {e}")


if __name__ == "__main__":
    main()
