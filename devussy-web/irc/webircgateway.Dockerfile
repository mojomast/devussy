FROM golang:1.22-alpine AS builder
WORKDIR /app
RUN apk add --no-cache git

# Fetch WebIRC Gateway source
RUN git clone https://github.com/kiwiirc/webircgateway.git .

# Build the binary
RUN go build -o webircgateway

FROM alpine:3.19
WORKDIR /app

# Copy compiled gateway
COPY --from=builder /app/webircgateway /usr/local/bin/webircgateway

# Config will be mounted at /config/gateway.conf
EXPOSE 8080

CMD ["webircgateway", "--config=/config/gateway.conf"]
