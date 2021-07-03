from general import MultiThread

if __name__ == '__main__':
    def test(num1):
        print(num1)

    def testing(num):
        print(num)
        MultiThread(test, range(10), threads=10).mt()


    abc = ['a', 'b', 'c']
    MultiThread(testing, abc, threads=3).mt()
