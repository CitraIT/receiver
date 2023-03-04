import os
import socket
import pathlib
import pdb


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('0.0.0.0', 8000))
s.listen()
client, addr = s.accept()

client_data = client.recv(8196)
#print(client_data)

client_header, client_body = client_data.split(b'\r\n\r\n')
header_array = client_header.split(b'\r\n')

request_line = header_array.pop(0)
print(f'request line: %s' % request_line.decode())
request_headers = {}
for h in header_array:
    print(f'unpacking line %s' % h.decode())
    #pdb.set_trace()
    k,v = h.split(sep=b':', maxsplit=1)
    request_headers[k.decode().lower()] = v.decode()

# obter o boundary do upload
boundary = ''
if 'content-type' in request_headers:
    if 'multipart/form-data' in request_headers['content-type'].lower():
        content_type_parts = request_headers['content-type'].split(";")
        boundary = ''
        for i in content_type_parts:
            if 'boundary' in i:
                boundary = i.split('=')[-1]

print(f'found boundary: %s' % boundary)
boundary = f'--{boundary}'

if 'expect' in request_headers.keys():
    print(f'received a expect 100-continue')
    print(f'will read from socket till received boundary')
    client.sendall(b'HTTP/1.1 100 Continue\r\n\r\n')
    
    # process first request
    new_data = client.recv(8196)
    data_header, data_body = new_data.split(b'\r\n\r\n')
    data_headers = {}
    for header_line in data_header.split(b'\r\n'):
        # skip boundary
        if header_line.decode() == boundary:
            print(f'found boundary in header...')
            continue
        k,v = header_line.split(sep=b':', maxsplit=1)
        data_headers[k.decode().lower()] = v.decode()
    
    # get filename
    #print(f'DEBUG: {data_headers}')
    if 'content-disposition' in data_headers and 'filename' in data_headers['content-disposition']:
        #filename="importa.zip"
        a1 = [ x.split('=')[-1] for x in data_headers['content-disposition'].split(';') if 'filename' in x ]
        upload_filename = a1[0].replace('"','')
        
    
    if not upload_filename:
        raise "coul'd get a valid filename in attachment."
    
    print(f'writing to file {upload_filename}')
    
    target_upload_file = pathlib.Path(os.getcwd(), upload_filename)
    myfile = open(target_upload_file, 'wb')
    
    
    if len(data_body) > 1:
        #print(f'first request has content.')
        myfile.write(data_body)
        print(f'wrote {len(data_body)}')
    
    end_boundary = f'\r\n{boundary}--\r\n'.encode()
    #while not data_body.endswith(end_boundary):
    last_packet = False
    while True:
        data_body = client.recv(8196)
        if data_body.endswith(end_boundary):
            data_body = data_body.replace(end_boundary, b'')
            last_packet = True
        myfile.write(data_body)
        myfile.flush()
        print(f'wrote {len(data_body)}')
        if last_packet:
            print(f'that was the last chunk! DONE.')
            break

client.sendall(b'HTTP/1.1 200 OK\r\n\r\n')
myfile.close()    
client.close()
s.close()
