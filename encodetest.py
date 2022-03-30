
a = u"狗"
a_gb2312 = a.encode('gb2312')
print(a_gb2312)

a_gb2312 = str(a_gb2312)
a_gb2312 = a_gb2312.replace("\\x", "")
print(a_gb2312)
print(a_gb2312[2:-1])