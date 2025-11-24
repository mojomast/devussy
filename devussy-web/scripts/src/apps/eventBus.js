"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.useEventBus = exports.EventBusProvider = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
class EventBus {
    constructor() {
        this.listeners = {};
    }
    emit(event, payload) {
        const handlers = this.listeners[event];
        if (!handlers)
            return;
        handlers.forEach((fn) => {
            try {
                fn(payload);
            }
            catch (err) {
                console.error("[EventBus] handler error for", event, err);
            }
        });
    }
    subscribe(event, cb) {
        if (!this.listeners[event]) {
            this.listeners[event] = new Set();
        }
        this.listeners[event].add(cb);
        return () => {
            this.listeners[event].delete(cb);
            if (this.listeners[event] && this.listeners[event].size === 0) {
                delete this.listeners[event];
            }
        };
    }
}
const EventBusContext = (0, react_1.createContext)(null);
const EventBusProvider = ({ children }) => {
    const busRef = (0, react_1.useRef)(null);
    if (!busRef.current) {
        busRef.current = new EventBus();
    }
    return ((0, jsx_runtime_1.jsx)(EventBusContext.Provider, { value: busRef.current, children: children }));
};
exports.EventBusProvider = EventBusProvider;
const useEventBus = () => {
    const bus = (0, react_1.useContext)(EventBusContext);
    if (!bus) {
        throw new Error("useEventBus must be used within an EventBusProvider");
    }
    return bus;
};
exports.useEventBus = useEventBus;
