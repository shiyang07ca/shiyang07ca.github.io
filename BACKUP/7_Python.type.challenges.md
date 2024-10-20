# [Python type challenges](https://github.com/shiyang07ca/shiyang07ca.github.io/issues/7)

- [Python 为什么要需要类型 1](#python-为什么要需要类型-1)
  - [一些有用的资料](#一些有用的资料)
- [Python 类型基础](#python-类型基础)
  - [常见关键字](#常见关键字)
    - [Union](#union)
    - [Optional](#optional)
    - [TypeVar](#typevar)
    - [Any](#any)
  - [类型别名 (TypeAlias)](#类型别名-typealias)
  - [NewType](#newtype)
- [函数](#函数)
  - [可调用对象（Callable）](#可调用对象callable)
  - [Paramspec](#paramspec)
  - [Concatenate](#concatenate)
  - [unpack](#unpack)
  - [TypeVarTuple](#typevartuple)
    - [示例](#示例)
    - [示例 2](#示例-2)
  - [TypeGuard](#typeguard)
- [类](#类)
  - [ClassVar](#classvar)
  - [Self](#self)
- [泛型（Generic）](#泛型generic)
  - [TypeVar](#typevar-1)
  - [泛型函数（Generic Functions）](#泛型函数generic-functions)
  - [泛型类](#泛型类)
    - [泛型类定义](#泛型类定义)
  - [泛型和继承](#泛型和继承)
  - [overload](#overload)
  - [Protocol](#protocol)
  - [callable-protocol](#callable-protocol)
- [TypedDict](#typeddict)
- [其他](#其他)
  - [Literal](#literal)
  - [LiteralString](#literalstring)
  - [装饰器（decorator）](#装饰器decorator)
  - [描述器（descriptor）](#描述器descriptor)
  - [生成器（generator）](#生成器generator)
  - [never](#never)
  - [buffer](#buffer)
- [TODO: 协变，逆变，不变(covariant, contravariant, invariant)](#todo-协变逆变不变covariant-contravariant-invariant)
- [排查工具](#排查工具)
  - [使用 `reveal_type` 查看推断类型](#使用-reveal_type-查看推断类型)
  - [使用 `cast` 来强制指定类型：](#使用-cast-来强制指定类型)
  - [使用类型忽略标记禁用一行中的错误：](#使用类型忽略标记禁用一行中的错误)
- [生成 type annotation](#生成-type-annotation)
- [一些类型检查工具](#一些类型检查工具)


## Python 为什么要需要类型 [1]

- 标注所有参数和返回类型可以更容易理解代码，更易于修改或添加代码
- 在使用库时，可以更容易地检查类型，方便 IDE 代码补全以及检查错误参数
- 可以使使用 linter 工具可以提前发现类型错误
- 运行时数据验证工具，例如：[pydantic](https://github.com/pydantic/pydantic)


### 一些有用的资料

- [The state of type hints in Python · Tech articles by Bernát Gábor](https://bernat.tech/posts/the-state-of-type-hints-in-python/)
- [laike9m/Python-Type-Challenges: Master Python typing (type hints) with interactive online exercises!](https://github.com/laike9m/Python-Type-Challenges)
- [PEP 484 – Type Hints | peps.python.org](https://peps.python.org/pep-0484/)
- [Python 类型体操训练（一）-- 基础篇 | 用代码打点酱油的chaofa](https://bruceyuan.com/post/python-type-challenge-basic.html)

## Python 类型基础

### 常见关键字

#### Union

`Union[X, Y]` 等价于 `X | Y` (3.10 及以上)，意味着满足 `X` 或 `Y` 之一。
参数必须是某种类型(`X` 或 `Y`)，且至少有一个。

#### Optional

`Optional[X]` 等价于 `X | None` （或 `Union[X, None]` ） 。


#### TypeVar

可以使用 `TypeVar` 构造定义它自己的通用容器：
```python
T = TypeVar('T')
class Magic(Generic[T]):
      def __init__(self, value: T) -> None:
         self.value : T = value

 def square_values(vars: Iterable[Magic[int]]) -> None:
     v.value = v.value * v.value
```

`TypeVar` 还可以通过指定多个类型参数来创建泛型，表示参数可以是这些类型之一：
```python
T = TypeVar('T', int, str)  # T 可以是 int 或 str

def add(x: T, y: T) -> T:
    return x + y
```


#### Any

可以使用 `Any` 类型可以在不需要的地方禁用类型检查：

```python
def foo(item: Any) -> int:
     item.bar()
```     


### 类型别名 (TypeAlias)
类型别名是使用 `type` 语句来定义的，它将创建一个 `TypeAliasType` 的实例。 在这个
示例中，Vector 和 list[float] 将被静态类型检查器等同处理:
```python
type Vector = list[float]

def scale(scalar: float, vector: Vector) -> Vector:
    return [scalar * num for num in vector]

# 通过类型检查；浮点数列表是合格的 Vector。
new_vector = scale(2.0, [1.0, -4.2, 5.4])
```

`type` 语句是在 Python 3.12 中新增加的。 为了向下兼容，类型别名也可以通过简单的赋
值来创建:

```python 
Vector = list[float]
```
也可以用 TypeAlias 标记来显式说明这是一个类型别名：

```python
from typing import TypeAlias

Vector: TypeAlias = list[float]
```

### NewType

`NewType` 用于创建一个新的类型，它与原始类型具有相同的值，但类型检查器会将其视为
不同的类型。

```python
from typing import NewType

UserId = NewType('UserId', int)
some_id = UserId(524313)
```

静态类型检查器把新类型当作原始类型的子类，这种方式适用于捕捉逻辑错误：

```python
def get_user_name(user_id: UserId) -> str:
    ...

# 通过类型检查
user_a = get_user_name(UserId(42351))

# 未通过类型检查；整数不能作为 UserId
user_b = get_user_name(-1)
```

>  **备注** 请记住使用类型别名将声明两个类型是相互 等价 的。 使用 type Alias =
 Original 将使静态类型检查器在任何情况下都把 Alias 视为与 Original 完全等价。 这
在你想要简化复杂的类型签名时会很有用处。
反之，NewType 声明把一种类型当作另一种类型的 子类型。Derived =
NewType('Derived', Original) 时，静态类型检查器把 Derived 当作 Original 的 子类
，即，Original 类型的值不能用在预期 Derived 类型的位置。这种方式适用于以最小运行
时成本防止逻辑错误。


## 函数

### 可调用对象（Callable）

`Callable[[int], str]` 表示一个接受 `int` 类型的单个形参并返回一个 `str` 的函数。


```python
from collections.abc import Callable, Awaitable

def feeder(get_next_item: Callable[[], str]) -> None:
    ...  # 函数体

def async_query(on_success: Callable[[int], None],
                on_error: Callable[[int, Exception], None]) -> None:
    ...  # 函数体

async def on_update(value: str) -> None:
    ...  # 函数体

callback: Callable[[str], Awaitable[None]] = on_update
```

如果不确定参数数量，可以使用 `Callable[..., ReturnType]` 来表示任意数量的参数


### Paramspec

ParamSpec 是 Python 3.10 引入的，它允许你在类型提示中使用可变数量和类型的参数。
主要用于以下场景:
1. 定义高阶函数(接受或返回其他函数的函数)的类型
2. 保留原始函数的参数签名信息

```python
from typing import Callable, ParamSpec, TypeVar

# Before 3.12 you have to write:
# P = ParamSpec('P')  # 定义 ParamSpec
# R = TypeVar('R')  # 定义返回类型的 TypeVar

def add_logging[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {f.__name__}")
        return f(*args, **kwargs)
    return wrapped

@add_logging
def greet(name: str) -> str:
    return f"Hello, {name}!"

result = greet("Alice")
print(result)
```


### Concatenate
主要用于与 Callable 和 ParamSpec（参数规格）配合使用。它允许我们在类型提示中将多
个参数类型拼接在一起，从而创建更灵活的函数类型提示。

```python
from typing import Concatenate, Callable, ParamSpec, TypeVar

P = ParamSpec('P')  # 定义一个参数规格
T = TypeVar('T')    # 定义一个泛型类型

def decorator(func: Callable[Concatenate[int, P], T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print("Adding an integer argument")
        return func(42, *args, **kwargs)  # 在调用原函数时插入一个整数参数
    return wrapper
```

### unpack
Python 3.11 开始引入了类型参数展开（Type Parameter Unpacking），可以通过 * 操作
符解包类型参数。这允许你在类型提示中处理变长的参数列表和泛型参数。

Unpack 也可以与 typing.TypedDict 一起使用以便在函数签名中对 **kwargs 进行类型标
注

``` python
"""
TODO:

`foo` expects two keyword arguments - `name` of type `str`, and `age` of type `int`.
"""

from typing import Unpack, TypedDict


class Person(TypedDict):
    name: str
    age: int


def foo(**kwargs: Unpack[Person]):
    ...


## End of your code ##
person: Person = {"name": "The Meaning of Life", "age": 1983}
foo(**person)
foo(**{"name": "Brian", "age": 30})

foo(**{"name": "Brian"})  # expect-type-error
person2: dict[str, object] = {"name": "Brian", "age": 20}
foo(**person2)  # expect-type-error
foo(**{"name": "Brian", "age": "1979"})  # expect-type-error
```


### TypeVarTuple

TypeVarTuple 可以定义“变长元组”（variadic tuples）类型。这种类型提示可以捕获多个
类型，并且允许元组长度动态变化。它类似于泛型中的 TypeVar，但 TypeVarTuple 是专门
用于处理可变数量的类型参数的。

TypeVarTuple 用于定义一组任意数量的类型参数，它们可以一起表示一个变长的元组或任
意长的参数列表。

TypeVarTuple 定义一个类型元组，它可以代表任意数量的类型。
Unpack 用于从 TypeVarTuple 中提取类型参数，并应用到函数或类中。

#### 示例
定义一个函数，它接受一个 Tuple，其中的元素可以是任意类型，并返回这个元组。我们可
以使用 TypeVarTuple 来定义这样一个函数：

```python
from typing import TypeVarTuple, Tuple, Unpack

Ts = TypeVarTuple('Ts')  # 定义一个类型元组 Ts

def my_tuple_func(t: Tuple[Unpack[Ts]]) -> Tuple[Unpack[Ts]]:
    return t

# 我们可以使用这个函数处理不同类型和长度的元组：
print(my_tuple_func((1, 'a', 3.14)))  # 输出：(1, 'a', 3.14)
print(my_tuple_func((True,)))         # 输出：(True,)
```
在这个例子中：
- `Ts = TypeVarTuple('Ts')` 定义了一个类型变量 `Ts`，它可以代表一组类型。
- `my_tuple_func` 函数接受一个 Tuple，这个元组的类型是由 `Unpack[Ts]` 解包的。
- `Tuple[Unpack[Ts]]` 表示这个元组可以包含多个类型。


#### 示例 2
```python
"""
TODO:

Define an `Array` type that supports element-wise addition of arrays with identical dimensions and types.
"""

from typing import Generic, TypeVar, TypeVarTuple, assert_type

T = TypeVar("T")
Ts = TypeVarTuple("Ts")


class Array(Generic[*Ts]):
    def __add__(self, other: "Array[*Ts]") -> "Array[*Ts]":
        ...


## End of your code ##
from typing import assert_type

a: Array[float, int] = Array()
b: Array[float, int] = Array()
assert_type(a + b, Array[float, int])

c: Array[float, int, str] = Array()
assert_type(a + c, Array[float, int, str])  # expect-type-error
```


---




```python
P = ParamSpec('P')
R = TypeVar('R')

def add_logging(f: Callable[P, R]) -> Callable[P, R]:
    ...
```


### TypeGuard

`TypeGuard` 是一种类型提示，用于告诉类型检查器某个函数在运行时能够对变量的类型进
行校验和收缩。它通常用于类型推断工具（例如 `mypy`）来缩小类型范围。

假设我们有一个函数 `is_str_list`，它接受一个 `list` 并检查该列表中的所有元素是否都是
字符串。我们希望在通过该检查后，类型检查器能够推断出列表是由字符串组成的。

```python
from typing import List, TypeGuard, Union

def is_str_list(values: List[Union[str, int]]) -> TypeGuard[List[str]]:
    return all(isinstance(v, str) for v in values)

# 使用示例
my_list: List[Union[str, int]] = ["a", "b", 1]

if is_str_list(my_list):
    # 这里类型检查器会推断 my_list 的类型为 List[str]
    print("All elements are strings")
```
在这个例子中：

`is_str_list` 是一个自定义类型守卫函数，使用 `TypeGuard` 来标注返回值。
返回类型 `TypeGuard[List[str]]` 告诉类型检查器，如果 `is_str_list` 返回 `True`，
则传入的 `values` 类型会被认为是 `List[str]`。

因此，当我们在 `if` 语句中调用 `is_str_list` 后，`my_list` 的类型会自动缩小到
`List[str]`，而不再是最初的 `List[Union[str, int]]`。

## 类

### ClassVar

`ClassVar` 注解是指，给定属性应当用作类变量，而不应设置在类实例上。用法如下：
```python
class Starship:
    stats: ClassVar[dict[str, int]] = {} # 类变量
    damage: int = 10                     # 实例变量
```

```python
"""
TODO:

Class `Foo` has a class variable `bar`, which is an integer.
"""
from typing import ClassVar


class Foo:
    bar: ClassVar[int]
    """Hint: No need to write __init__"""


## End of your code ##
Foo.bar = 1
Foo.bar = "1"  # expect-type-error
Foo().bar = 1  # expect-type-error
```

### Self
表示当前闭包内的类

```python
from typing import Self, reveal_type

class Foo:
    def return_self(self) -> Self:
        ...
        return self

class SubclassOfFoo(Foo): pass

reveal_type(Foo().return_self())  # 揭示的类型为 "Foo"
reveal_type(SubclassOfFoo().return_self())  # 揭示的类型为 "SubclassOfFoo"
```
此注解在语法上等价于以下代码，但形式更为简洁：
```python
from typing import TypeVar

Self = TypeVar("Self", bound="Foo")

class Foo:
    def return_self(self: Self) -> Self:
        ...
        return self
```
通常来说，如果某些内容返回 `self`，如上面的示例所示，您应该使用 `Self` 作为返回
值注解。如果 `Foo.return_self` 被注解为返回 `"Foo"`，那么类型检查器将推断从
`SubclassOfFoo.return_self` 返回的对象是 `Foo` 类型，而不是 `SubclassOfFoo`。


challenge:

```python
"""
TODO:

`return_self` should return an instance of the same type as the current enclosed class.
"""

from typing import Self


class Foo:
    def return_self(self) -> Self:
        ...


# Another solution using TypeVar
# from typing import TypeVar
#
# T = TypeVar('T', bound='Foo')
#
# class Foo:
#     def return_self(self: T) -> T:
#         ...


## End of your code ##
class SubclassOfFoo(Foo):
    pass


f: Foo = Foo().return_self()
sf: SubclassOfFoo = SubclassOfFoo().return_self()

sf: SubclassOfFoo = Foo().return_self()  # expect-type-error
```

## 泛型（Generic）

### TypeVar

`TypeVar` 可以用来定义一个类型变量，它可以代表任意类型，并且可以在多个地方重用。

泛型函数和类可以通过使用 `类型形参语法` 来实现参数化:

```python
from collections.abc import Sequence

def first[T](l: Sequence[T]) -> T:  # 函数是 TypeVar "T" 泛型
    return l[0]
```

`TypeVar` 提供 `bound` 参数可以约束它只能是某种类型的子类。
```python

from typing import TypeVar

# T 必须是 int 或其子类
T = TypeVar('T', bound=int)

def double(x: T) -> T:
    return x * 2
```


### 泛型函数（Generic Functions）
```python
from typing import TypeVar

T = TypeVar('T')  # 定义一个泛型 T

def identity(x: T) -> T:
    return x

# >= 3.12 推荐写法
def identity[T](x: T) -> T:
    return x
```


### 泛型类
在泛型类中，类的属性和方法可以适应不同的数据类型。通过 Generic 类，我们可以将类
声明为泛型类。


#### 泛型类定义
例如，我们可以定义一个简单的容器类，它能够存储任意类型的数据：

```python
from logging import Logger

# `T` 是类体内部有效的类型
class LoggedVar[T]:
    def __init__(self, value: T, name: str, logger: Logger) -> None:
        self.name = name
        self.logger = logger
        self.value = value

    def set(self, new: T) -> None:
        self.log('Set ' + repr(self.value))
        self.value = new

    def get(self) -> T:
        self.log('Get ' + repr(self.value))
        return self.value

    def log(self, message: str) -> None:
        self.logger.info('%s: %s', self.name, message)
```

泛型类隐式继承自 `Generic`。为了与 Python 3.11 及更低版本兼容，也允许显式地从
`Generic` 继承以表示泛型类：

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class LoggedVar(Generic[T]):
    ...
```



### 泛型和继承


在面向对象编程中，泛型类可以与继承结合使用，允许子类继承父类的泛型行为。
```python
from typing import Generic, TypeVar

T = TypeVar('T')

class Animal(Generic[T]):
    def speak(self, sound: T) -> None:
        print(f"The animal says {sound}")

class Dog(Animal[str]):
    pass

dog = Dog()
dog.speak("woof")  # 输出：The animal says woof
```
在这个例子中，`Animal` 是一个泛型类，`Dog` 继承了 `Animal`，并将泛型 `T` 限定为
`str` 类型。


### overload

`@overload` 装饰器可以用来声明同一函数的多个版本，每个版本有不同的参数类型和返回值
类型，但在运行时不会实际执行。mypy 会根据参数类型来推断正确的类型签名。

非 `@overload` 装饰的定义将在运行时使用但应被类型检查器忽略。在运行时，直接调用以
`@overload` 装饰的函数将引发 NotImplementedError。

challenge:
```python
"""
TODO:
`process` is a function that takes one argument `response`
- When `response` is bytes, `process` returns a string
- When `response` is an integer, `process` returns tuple[int, str]
- When `response` is None, `process` returns None
"""
from typing import overload


@overload
def process(response: None) -> None:
    ...


@overload
def process(response: int) -> tuple[int, str]:
    ...


@overload
def process(response: bytes) -> str:
    ...


def process(response: int | bytes | None) -> str | None | tuple[int, str]:
    ...


## End of your code ##
from typing import assert_type

assert_type(process(b"42"), str)
assert_type(process(42), tuple[int, str])
assert_type(process(None), None)

assert_type(process(42), str)  # expect-type-error
assert_type(process(None), str)  # expect-type-error
assert_type(process(b"42"), tuple[int, str])  # expect-type-error
assert_type(process(None), tuple[int, str])  # expect-type-error
assert_type(process(42), str)  # expect-type-error
assert_type(process(None), str)  # expect-type-error
```

### Protocol

用于定义“结构化子类型”（structural subtyping），也称为“鸭子类型”。`Protocol`  允
许我们通过“接口”来定义一个类型，而不强制要求对象必须显式继承这些接口。只要一个对
象实现了所需的方法或属性，它就可以被认为符合某个 `Protocol`。

``` python
"""
TODO:
    Define a protocol for class `SupportsQuack` that supports a "quack" method.
"""

from typing import Protocol


class SupportsQuack(Protocol):
    def quack(self) -> None:
        ...


## End of your code ##
class Duck:
    def quack(self) -> None:
        print("quack!")


class Dog:
    def bark(self) -> None:
        print("bark!")


duck: SupportsQuack = Duck()
dog: SupportsQuack = Dog()  # expect-type-error
```  


### callable-protocol

```python
"""
TODO:

Define a callable type that accepts a string parameter called `name` and returns None.
"""
from typing import Protocol


class SingleStringInput(Protocol):
    def __call__(self, name: str) -> None:
        ...


## End of your code ##
def accept_single_string_input(func: SingleStringInput) -> None:
    func(name="name")


def string_name(name: str) -> None:
    ...


def string_value(value: str) -> None:
    ...


def return_string(name: str) -> str:
    return name


accept_single_string_input(string_name)
accept_single_string_input(string_value)  # expect-type-error
accept_single_string_input(return_string)  # expect-type-error
```



## TypedDict

TypedDict 声明一个字典类型，字典定义一个具有特定键和值类型的字典结构，可以像定义
类一样定义字典的键和值的类型，确保字典的键和值符合预期。 可以使用 NotRequired 将
单独的键标记为非必要。


```python
"""
TODO:

Define a class `Student` that represents a dictionary with three keys:
- name, a string
- age, an integer
- school, a string
"""
from typing import TypedDict

class Student(TypedDict):
    name: str
    age: int
    school: str

a: Student = {"name": "Tom", "age": 15, "school": "Hogwarts"}
a: Student = {"name": 1, "age": 15, "school": "Hogwarts"}  # expect-type-error
a: Student = {(1,): "Tom", "age": 2, "school": "Hogwarts"}  # expect-type-error
a: Student = {"name": "Tom", "age": "2", "school": "Hogwarts"}  # expect-type-error
a: Student = {"name": "Tom", "age": 2}  # expect-type-error
assert Student(name="Tom", age=15, school="Hogwarts") == dict(
    name="Tom", age=15, school="Hogwarts"
)
```

默认情况下，所有的键都必须出现在一个 TypedDict 中。可以使用 NotRequired 将单独
的键标记为非必要

``` python
"""
TODO:

Define a class `Student` that represents a dictionary with three keys:
- name, a string
- age, an integer
- school, a string

Note: school can be optional
"""

from typing import TypedDict, NotRequired

class Student(TypedDict):
    name: str
    age: int
    school: NotRequired[str]

a: Student = {"name": "Tom", "age": 15}
a: Student = {"name": "Tom", "age": 15, "school": "Hogwarts"}
a: Student = {"name": 1, "age": 15, "school": "Hogwarts"}  # expect-type-error
a: Student = {(1,): "Tom", "age": 2, "school": "Hogwarts"}  # expect-type-error
a: Student = {"name": "Tom", "age": "2", "school": "Hogwarts"}  # expect-type-error
a: Student = {"z": "Tom", "age": 2}  # expect-type-error
assert Student(name="Tom", age=15) == dict(name="Tom", age=15)
assert Student(name="Tom", age=15, school="Hogwarts") == dict(
    name="Tom", age=15, school="Hogwarts"
)

```

使用 total=False 时，TypedDict 中单独的键可以使用 Required 标记为必要的

```python
"""
TODO:

Define a class `Person` that represents a dictionary with five string keys:
    name, age, gender, address, email

The value of each key must be the specified type:
    name - str, age - int, gender - str, address - str, email - str

Note: Only `name` is required
"""

from typing import TypedDict, Required


class Person(TypedDict, total=False):
    name: Required[str]
    age: int
    gender: str
    address: str
    email: str


# Alternative soltion:
#
# Person = TypedDict('Person', {
#     name: Required[str],
#     age: int,
#     gender: str,
#     address: str,
#     email: str,
# }, total=False):

## End of your code ##
a: Person = {
    "name": "Capy",
    "age": 1,
    "gender": "Male",
    "address": "earth",
    "email": "capy@bara.com",
}
a: Person = {"name": "Capy"}
a: Person = {"age": 1, "gender": "Male", "address": "", "email": ""} # expect-type-error
```




## 其他

### Literal
特殊类型注解形式，用于定义“字面值类型”。

Literal 可以用来向类型检查器说明被注解的对象具有与所提供的字面量之一相同的值。

```python
def validate_simple(data: Any) -> Literal[True]:  # 总是返回 True
    ...

type Mode = Literal['r', 'rb', 'w', 'wb']
def open_helper(file: str, mode: Mode) -> str:
    ...

open_helper('/some/path', 'r')      # 通过类型检查
open_helper('/other/path', 'typo')  # 类型检查错误
```

### LiteralString

只包括字符串字面值的的特殊类型。

```python
def run_query(sql: LiteralString) -> None:
    ...

def caller(arbitrary_string: str, literal_string: LiteralString) -> None:
    run_query("SELECT * FROM students")  # 可以
    run_query(literal_string)  # 可以
    run_query("SELECT * FROM " + literal_string)  # 可以
    run_query(arbitrary_string)  # 类型检查器错误
    run_query(  # 类型检查器错误
        f"SELECT * FROM students WHERE name = {arbitrary_string}"
    )
```

LiteralString 对于会因用户可输入任意字符串而导致问题的敏感 API 很有用。例如，上
述两处导致类型检查器报错的代码可能容易被 SQL 注入攻击。




### 装饰器（decorator）

```python
"""
TODO:

定义一个装饰器，它包装一个函数并返回一个具有相同签名的函数。
"""
from typing import Callable, TypeVar

# For Python < 3.12
#
# T = TypeVar("T", bound=Callable)
#
# def decorator(func: T) -> T:
#     return func


# For Python >= 3.12
def decorator[T: Callable](func: T) -> T:
    return func


## End of your code ##
@decorator
def foo(a: int, *, b: str) -> None:
    ...


@decorator
def bar(c: int, d: str) -> None:
    ...


foo(1, b="2")
bar(c=1, d="2")

foo(1, "2")  # expect-type-error
foo(a=1, e="2")  # expect-type-error
decorator(1)  # expect-type-error
```

- TODO:
```python
"""
TODO:

定义一个装饰器，它包装一个函数并返回一个具有相同签名的函数。
这个装饰器接受一个名为 `message` 的字符串类型参数。
"""
from collections.abc import Callable
from typing import TypeVar

# For Python < 3.12
#
# T = TypeVar("T", bound=Callable)
#
# def decorator(message: str) -> Callable[[T], T]:
#     return func


# For Python >= 3.12
def decorator[T: Callable](message: str) -> Callable[[T], T]:
    ...


## End of your code ##
@decorator(message="x")
def foo(a: int, *, b: str) -> None:
    ...


@decorator  # expect-type-error
def bar(a: int, *, b: str) -> None:
    ...


foo(1, b="2")
foo(1, "2")  # expect-type-error
foo(a=1, e="2")  # expect-type-error
decorator(1)  # expect-type-error
```

### 描述器（descriptor）
`Self` 是一个特殊类型，表示当前闭包内的类。

```python
from typing import Self, reveal_type

class Foo:
    def return_self(self) -> Self:
        ...
        return self

class SubclassOfFoo(Foo): pass

reveal_type(Foo().return_self())  # 揭示的类型为 "Foo"
reveal_type(SubclassOfFoo().return_self())  # 揭示的类型为 "SubclassOfFoo"
```

此注解在语法上等价于以下代码，但形式更为简洁：
```python
from typing import TypeVar

Self = TypeVar("Self", bound="Foo")

class Foo:
    def return_self(self: Self) -> Self:
        ...
        return self
```


```python
"""
TODO:

Create a descriptor and annotate the __get__ method.
"""

from typing import Any, Self, overload


class Descriptor:
    # 如果 instance 是 None,表示是通过类访问的，返回描述符自身 (self)
    @overload
    def __get__(self, instance: None, owner: type) -> Self:
        ...

    # 通过实例访问的，返回一个字符串 "描述符值"
    @overload
    def __get__(self, instance: Any, owner: type) -> str:
        ...

    def __get__(self, instance: Any, owner: type) -> Self | str:
        ...


## End of your code ##
class TestClass:
    a = Descriptor()


def descriptor_self(x: Descriptor) -> None:
    ...


def string_value(x: str) -> None:
    ...


descriptor_self(TestClass.a)
string_value(TestClass().a)
descriptor_self(TestClass().a)  # expect-type-error
string_value(TestClass.a)  # expect-type-error
```


### 生成器（generator）

生成器可以使用泛型类型 `Generator[YieldType, SendType, ReturnType]` 来标。 例如:

```python
def echo_round() -> Generator[int, float, str]:
    sent = yield 0
    while sent >= 0:
        sent = yield round(sent)
    return 'Done'
```

```python
"""
TODO:

`gen` is a generator that yields a integer, and can accept a string sent to it.
It does not return anything.
"""

from collections.abc import Generator


def gen() -> Generator[int, str, None]:
    """You don't need to implement it"""
    ...


## End of your code ##
from typing import assert_type

generator = gen()
assert_type(next(generator), int)
generator.send("sss")
generator.send(3)  # expect-type-error
```

### never
Never 和 NoReturn 代表 底类型(Bottom Type)，一种没有成员的类型。
它们可被用于指明一个函数绝不会返回，例如 sys.exit():

```python
from typing import Never  # 或 NoReturn

def stop() -> Never:
    raise RuntimeError('no way')
```

或者用于定义一个绝不应被调用的函数，因为不存在有效的参数，例如 assert_never():

``` python
from typing import Never  # 或 NoReturn

def never_call_me(arg: Never) -> None:
    pass

def int_or_str(arg: int | str) -> None:
    never_call_me(arg)  # 类型检查器错误
    match arg:
        case int():
            print("It's an int")
        case str():
            print("It's a str")
        case _:
            never_call_me(arg)  # OK, arg is of type Never (or NoReturn)
```

Never 和 NoReturn 在类型系统中具有相同的含义并且静态类型检查器会以相同的方式对待这两者。



### buffer

- https://docs.python.org/zh-cn/3/c-api/buffer.html#bufferobjects

```python
"""
TODO:

Annotate the function `read_buffer`, which accepts anything that is a buffer.

See https://docs.python.org/3.12/reference/datamodel.html#object.__buffer__
"""

from collections.abc import Buffer


def read_buffer(b: Buffer):
    ...


## End of your code ##

from array import array


class MyBuffer:
    def __init__(self, data: bytes):
        self.data = bytearray(data)
        self.view = None

    def __buffer__(self, flags: int) -> memoryview:
        self.view = memoryview(self.data)
        return self.view


read_buffer(b"foo")
read_buffer(memoryview(b"foo"))
read_buffer(array("l", [1, 2, 3, 4, 5]))
read_buffer(MyBuffer(b"foo"))
read_buffer("foo")  # expect-type-error
read_buffer(1)  # expect-type-error
read_buffer(["foo"])  # expect-type-error
```



## TODO: 协变，逆变，不变(covariant, contravariant, invariant)



## 排查工具

### 使用 `reveal_type` 查看推断类型

```python
a = [4]
reveal_type(a)         # -> error: Revealed type is 'builtins.list[builtins.int*]'
```

### 使用 `cast` 来强制指定类型：
```python
from typing import List, cast
a = [4]
b = cast(List[int], a) # passes fine
c = cast(List[str], a) # type: List[str] # passes fine (no runtime check)
reveal_type(c)         # -> error: Revealed type is 'builtins.list[builtins.str]'
```

### 使用类型忽略标记禁用一行中的错误：

```python
x = confusing_function() # type: ignore # see mypy/issues/1167
```

## 生成 type annotation
1. `mypy stubgen` [mypy/mypy/stubgen.py at master · python/mypy](https://github.com/python/mypy/blob/master/mypy/stubgen.py)
2. `monkeytype` [Instagram/MonkeyType: A Python library that generates static type annotations by collecting runtime types](https://github.com/Instagram/MonkeyType)


## 一些类型检查工具

1. [mypy - Optional Static Typing for Python](https://mypy-lang.org/)
2. [microsoft/pyright: Static Type Checker for Python](https://github.com/microsoft/pyright)
3. [facebook/pyre-check: Performant type-checking for python.](https://github.com/facebook/pyre-check)
4. [google/pytype: A static type analyzer for Python code](https://github.com/google/pytype)


---


[1]: https://bernat.tech/posts/the-state-of-type-hints-in-python/

