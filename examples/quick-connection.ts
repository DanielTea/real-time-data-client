import { RealTimeDataClient } from "../src/client";
import { Message } from "../src/model";

const onMessage = (_: RealTimeDataClient, message: Message): void => {
    console.log(message.topic, message.type, message.payload);
};

const onConnect = (client: RealTimeDataClient): void => {
    // Subscribe to a topic
    client.subscribe({
        subscriptions: [
            {
                topic: "comments",
                type: "*", // "*"" can be used to connect to all the types of the topic
                //filters: `{"parentEntityID":20200,"parentEntityType":"Event"}`,
            },

            /*
            // Subscribe to more topics
            {
                topic: "activity",
                type: "trades",
                filters: `{"event_slug":"slug"} // filters: `{"market_slug":"slug"}
            },
            */
        ],
    });
    /*
    // Unsubscribe from a topic
    client.subscribe({
        subscriptions: [
            {
                topic: "activity",
                type: "trades",
            },
        ],
    });
    */
};

new RealTimeDataClient({ onConnect, onMessage }).connect();
