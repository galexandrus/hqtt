import datetime

from django.db import models
from django.utils import timezone


class Author(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "eduapp_authors"

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "eduapp_teachers"

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = "eduapp_students"

    def __str__(self):
        return self.name

    def lessons(self, product):
        if self.product_set.filter(title=product.title).first() is not None:
            return list(Lesson.objects.filter(product=product))
        else:
            return "У Вас нет доступа к этому продукту"

    def available_for_purchase(self):
        afp_list = []
        for product in list(Product.objects.all()):
            if self.product_set.filter(title=product.title).first() is None:
                afp_list.append({
                    "author": product.author.name,
                    "title": product.title,
                    "start": product.start.isoformat(),
                    "cost": product.cost,
                    "lessons_quan": product.lesson_set.count(),
                })
        return afp_list


class Product(models.Model):
    author = models.ForeignKey(Author,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True)
    title = models.CharField(max_length=128, unique=True)
    start = models.DateTimeField()
    cost = models.IntegerField()
    min_quan = models.IntegerField(default=1,
                                   help_text="минимальное количество студентов в группе для старта")
    max_quan = models.IntegerField(default=3,
                                   help_text="максимальное количество студентов в группе")
    students = models.ManyToManyField(Student)
    teachers = models.ManyToManyField(Teacher)

    class Meta:
        db_table = "eduapp_products"

    def __str__(self):
        return self.title

    def create_new_group(self):
        groups_count = Group.objects.filter(product=self).count()
        new_group = Group(name=f"{self.title}_{groups_count + 1}", product=self)
        new_group.save()
        return new_group

    def add_student(self, student):
        self.students.add(student)
        groups_count = Group.objects.filter(product=self).count()
        available_seats = groups_count * self.max_quan
        if self.students.count() > available_seats:
            group_to_fill = self.create_new_group()
            group_to_fill.add_student(student)
        else:
            group_to_fill = Group.objects.filter(product=self).first()
            for group in list(Group.objects.filter(product=self)):
                if group.students.count() < group_to_fill.students.count():
                    group_to_fill = group
            group_to_fill.add_student(student)


class Lesson(models.Model):
    name = models.CharField(max_length=128, unique=True)
    link = models.CharField(max_length=256)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = "eduapp_lessons"

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=128, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student)

    class Meta:
        db_table = "eduapp_groups"

    def __str__(self):
        return self.name

    def add_student(self, student):
        if self.students.count() < self.product.max_quan:
            self.students.add(student)
        else:
            raise Exception(f"Группа {self.name} уже заполнена")
